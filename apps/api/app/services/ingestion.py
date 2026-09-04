import os
import glob
import uuid
import datetime
import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.warp import transform_bounds
from shapely.geometry import box
from sqlalchemy.orm import Session
from ..models.geospatial import SatelliteScene, SatelliteTile
from .minio_client import minio_client
from .embeddings import embedding_service
from PIL import Image

class IngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.minio = minio_client
        self.bucket = "geoscope"
        
    def process_directory(self, dir_path: str):
        # Scan for raw satellite imagery (GeoTIFFs)
        search_pattern = os.path.join(dir_path, "**/*.tif")
        files = glob.glob(search_pattern, recursive=True)
        
        if not files:
            return {"status": "error", "message": f"No .tif files found in {dir_path}"}
            
        results = []
        for file_path in files:
            res = self.process_file(file_path)
            results.append(res)
            
        return {"status": "success", "processed_files": len(results), "details": results}

    def process_file(self, file_path: str):
        scene_id = f"SCENE_{uuid.uuid4().hex[:8]}"
        
        try:
            mask_file_path = file_path.replace('.tif', '_mask.tif')
            has_mask = os.path.exists(mask_file_path)
            
            with rasterio.open(file_path) as src:
                # Extract bounds and convert to WGS84
                bounds = src.bounds
                if src.crs and src.crs.to_epsg() != 4326:
                    wgs84_bounds = transform_bounds(src.crs, 'EPSG:4326', *bounds)
                else:
                    wgs84_bounds = bounds
                    
                scene_geom = box(*wgs84_bounds).wkt
                scene_wkt = f"SRID=4326;{scene_geom}"
                
                # Mock metadata if not present in tags
                tags = src.tags()
                acq_time = tags.get('ACQUISITION_TIME', datetime.datetime.utcnow().isoformat())
                if isinstance(acq_time, str):
                    try:
                        acq_time = datetime.datetime.fromisoformat(acq_time)
                    except ValueError:
                        acq_time = datetime.datetime.utcnow()
                        
                cloud_cover = float(tags.get('CLOUD_COVER', 0.0))
                platform = tags.get('PLATFORM', 'Unknown')
                
                new_scene = SatelliteScene(
                    id=scene_id,
                    acquisition_time=acq_time,
                    cloud_cover=cloud_cover,
                    platform=platform,
                    geom=scene_wkt
                )
                self.db.add(new_scene)
                
                # Tiling logic (e.g., 512x512)
                tile_size = 512
                meta = src.meta.copy()
                meta.update({
                    "driver": "COG",
                    "height": tile_size,
                    "width": tile_size,
                    "compress": "deflate"
                })
                
                tiles_created = 0
                mask_src = rasterio.open(mask_file_path) if has_mask else None
                try:
                    for row in range(0, src.height, tile_size):
                        for col in range(0, src.width, tile_size):
                            window = Window(col, row, tile_size, tile_size)
                        
                        # Calculate window bounds in WGS84
                        win_bounds = src.window_bounds(window)
                        if src.crs and src.crs.to_epsg() != 4326:
                            w_wgs84_bounds = transform_bounds(src.crs, 'EPSG:4326', *win_bounds)
                        else:
                            w_wgs84_bounds = win_bounds
                            
                        tile_geom = box(*w_wgs84_bounds).wkt
                        tile_wkt = f"SRID=4326;{tile_geom}"
                        
                        # Read data for the tile
                        data = src.read(window=window)
                        
                        # Handle partial tiles at the edges
                        if data.shape[1] < tile_size or data.shape[2] < tile_size:
                            # Skip partial tiles or pad them. We will skip them for simplicity here.
                            continue
                            
                        # Save tile locally first (temp)
                        tile_id = f"{scene_id}_tile_{row}_{col}"
                        temp_path = f"/tmp/{tile_id}.tif"
                        
                        # Update transform for the specific window
                        win_transform = src.window_transform(window)
                        meta.update({"transform": win_transform})
                        
                        with rasterio.open(temp_path, 'w', **meta) as dest:
                            dest.write(data)
                            
                        # Upload to MinIO
                        minio_path = f"tiles/{scene_id}/{tile_id}.tif"
                        self.minio.fput_object(self.bucket, minio_path, temp_path)
                        
                        # Handle mask tile
                        if has_mask:
                            mask_data = mask_src.read(window=window)
                            mask_meta = mask_src.meta.copy()
                            mask_meta.update({
                                "driver": "COG",
                                "height": tile_size,
                                "width": tile_size,
                                "compress": "deflate",
                                "transform": win_transform
                            })
                            temp_mask_path = f"/tmp/{tile_id}_mask.tif"
                            with rasterio.open(temp_mask_path, 'w', **mask_meta) as mask_dest:
                                mask_dest.write(mask_data)
                            
                            mask_minio_path = f"masks/{scene_id}/{tile_id}_mask.tif"
                            self.minio.fput_object(self.bucket, mask_minio_path, temp_mask_path)
                            os.remove(temp_mask_path)
                        
                        # Generate real embedding using CLIP
                        try:
                            with Image.open(temp_path) as img:
                                real_embedding = embedding_service.get_image_embedding(img)
                        except Exception as e:
                            print(f"Error generating embedding: {e}")
                            real_embedding = [0.0] * 512
                            
                        os.remove(temp_path)
                        
                        tile = SatelliteTile(
                            id=tile_id,
                            scene_id=scene_id,
                            minio_path=f"{self.bucket}/{minio_path}",
                            embedding=real_embedding,
                            geom=tile_wkt
                        )
                        self.db.add(tile)
                        tiles_created += 1
                finally:
                    if mask_src:
                        mask_src.close()
                        
            self.db.commit()
            return {"status": "success", "scene_id": scene_id, "tiles_created": tiles_created}
            
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "file": file_path, "message": str(e)}
