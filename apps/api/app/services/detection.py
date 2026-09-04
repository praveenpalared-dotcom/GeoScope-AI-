import os
import numpy as np
import rasterio
from rasterio.features import shapes, geometry_mask
from rasterio.warp import reproject as rasterio_reproject, Resampling
from shapely.geometry import shape
from shapely.ops import transform as shapely_transform
from shapely.validation import make_valid
from geoalchemy2.shape import to_shape
from pyproj import Transformer
from sqlalchemy.orm import Session
from ..models.geospatial import TemporalPair, ChangeDetection, SatelliteTile
from .minio_client import minio_client

class ChangeDetectionService:
    def __init__(self, db: Session):
        self.db = db
        self.minio = minio_client
        self.bucket = "geoscope"
        
    def reproject_geometry_to_wgs84(self, geometry, transformer):
        if transformer:
            return shapely_transform(transformer.transform, geometry)
        return geometry

    def baseline_change_detection(self, pair_id: int, use_ai: bool = False):
        pair = self.db.query(TemporalPair).filter(TemporalPair.id == pair_id).first()
        if not pair:
            raise Exception("TemporalPair not found")
            
        # Get tiles for before and after scenes
        before_tiles = self.db.query(SatelliteTile).filter(SatelliteTile.scene_id == pair.before_scene_id).all()
        after_tiles = self.db.query(SatelliteTile).filter(SatelliteTile.scene_id == pair.after_scene_id).all()
        
        if not before_tiles or not after_tiles:
            raise Exception("Missing tiles for scenes")
            
        # Contextual Validation (Milestone 7): 
        # Lower confidence if the source scenes have high cloud cover.
        base_confidence = 0.85
        if pair.before_scene.cloud_cover > 20.0 or pair.after_scene.cloud_cover > 20.0:
            base_confidence = 0.50 # High risk of false alarm due to clouds
            
        detections_made = 0
        
        for b_tile in before_tiles:
            b_geom = to_shape(b_tile.geom)
            
            # Find corresponding tile in after scene based on spatial intersection
            best_a_tile = None
            max_overlap = 0
            
            for a_tile in after_tiles:
                a_geom = to_shape(a_tile.geom)
                if b_geom.intersects(a_geom):
                    overlap = b_geom.intersection(a_geom).area
                    if overlap > max_overlap:
                        max_overlap = overlap
                        best_a_tile = a_tile
                        
            if best_a_tile and max_overlap > 0:
                b_path = f"/tmp/{b_tile.id}.tif"
                a_path = f"/tmp/{best_a_tile.id}.tif"
                
                try:
                    self.minio.fget_object(self.bucket, b_tile.minio_path.replace(f"{self.bucket}/", ""), b_path)
                    self.minio.fget_object(self.bucket, best_a_tile.minio_path.replace(f"{self.bucket}/", ""), a_path)
                    
                    b_mask_minio_path = f"masks/{pair.before_scene_id}/{b_tile.id}_mask.tif"
                    a_mask_minio_path = f"masks/{pair.after_scene_id}/{best_a_tile.id}_mask.tif"
                    b_mask_path = f"/tmp/{b_tile.id}_mask.tif"
                    a_mask_path = f"/tmp/{best_a_tile.id}_mask.tif"
                    
                    has_masks = False
                    try:
                        self.minio.fget_object(self.bucket, b_mask_minio_path, b_mask_path)
                        self.minio.fget_object(self.bucket, a_mask_minio_path, a_mask_path)
                        has_masks = True
                    except Exception as e:
                        print(f"Masks not found for pair {b_tile.id} and {best_a_tile.id}")
                    
                    with rasterio.open(b_path) as src_b, rasterio.open(a_path) as src_a:
                        if not src_b.crs or not src_a.crs:
                            raise ValueError("Missing CRS in raster tiles. Cannot perform CRS-safe detection.")

                        print(f"\n--- Processing Pair: Before Tile {b_tile.id}, After Tile {best_a_tile.id} ---")
                        print(f"Before CRS: {src_b.crs}")
                        print(f"After CRS: {src_a.crs}")
                        print(f"Before shape: {src_b.shape}, Original bounds: {src_b.bounds}")
                        print(f"After shape: {src_a.shape}, Original bounds: {src_a.bounds}")
                        
                        if use_ai:
                            # Read all 3 RGB bands and reshape for AI service (H, W, 3)
                            data_b = src_b.read([1, 2, 3]).transpose(1, 2, 0)
                            data_a = src_a.read([1, 2, 3]).transpose(1, 2, 0)
                        else:
                            data_b = src_b.read(1) # Read first band
                            data_a = src_a.read(1)
                        
                        # Handle nodata
                        nodata_b = src_b.nodata if src_b.nodata is not None else 0
                        nodata_a = src_a.nodata if src_a.nodata is not None else 0
                        
                        # Verify alignment, reproject if necessary
                        if (src_b.crs != src_a.crs or 
                            src_b.shape != src_a.shape or 
                            src_b.transform != src_a.transform):
                            
                            if use_ai:
                                # For multi-band arrays, transpose back to (C, H, W) for rasterio, then back to (H, W, C)
                                data_a_t = data_a.transpose(2, 0, 1)
                                data_a_aligned = np.empty((3, src_b.shape[0], src_b.shape[1]), dtype=data_a.dtype)
                                rasterio_reproject(
                                    source=data_a_t,
                                    destination=data_a_aligned,
                                    src_transform=src_a.transform,
                                    src_crs=src_a.crs,
                                    dst_transform=src_b.transform,
                                    dst_crs=src_b.crs,
                                    src_nodata=nodata_a,
                                    dst_nodata=nodata_a,
                                    resampling=Resampling.bilinear
                                )
                                data_a = data_a_aligned.transpose(1, 2, 0)
                            else:
                                data_a_aligned = np.empty_like(data_b)
                                rasterio_reproject(
                                    source=data_a,
                                    destination=data_a_aligned,
                                    src_transform=src_a.transform,
                                    src_crs=src_a.crs,
                                    dst_transform=src_b.transform,
                                    dst_crs=src_b.crs,
                                    src_nodata=nodata_a,
                                    dst_nodata=nodata_a,
                                    resampling=Resampling.bilinear
                                )
                                data_a = data_a_aligned
                            print("Reprojected AFTER tile onto BEFORE grid using Bilinear resampling.")
                        
                        print(f"Aligned dimensions: BEFORE {data_b.shape}, AFTER {data_a.shape}")
                        
                        if has_masks:
                            with rasterio.open(b_mask_path) as b_mask_src, rasterio.open(a_mask_path) as a_mask_src:
                                scl_b = b_mask_src.read(1)
                                scl_a = a_mask_src.read(1)
                                
                                if (src_b.crs != src_a.crs or src_b.shape != src_a.shape or src_b.transform != src_a.transform):
                                    scl_a_aligned = np.empty_like(scl_b)
                                    rasterio_reproject(
                                        source=scl_a,
                                        destination=scl_a_aligned,
                                        src_transform=a_mask_src.transform,
                                        src_crs=a_mask_src.crs,
                                        dst_transform=src_b.transform,
                                        dst_crs=src_b.crs,
                                        resampling=Resampling.nearest
                                    )
                                    scl_a = scl_a_aligned
                        
                        # Create valid mask
                        if use_ai:
                            # Valid if not nodata in any band
                            valid_mask = (np.sum(data_b == nodata_b, axis=-1) != 3) & (np.sum(data_a == nodata_a, axis=-1) != 3)
                        else:
                            valid_mask = (data_b != nodata_b) & (data_a != nodata_a)
                        
                        if has_masks:
                            exclude_classes = [0, 1, 3, 8, 9, 10, 11]
                            scl_valid = (~np.isin(scl_b, exclude_classes)) & (~np.isin(scl_a, exclude_classes))
                            valid_mask = valid_mask & scl_valid
                            print(f"Pixels excluded by SCL Cloud Mask: {np.sum(~scl_valid)}")
                            
                        num_valid = np.sum(valid_mask)
                        print(f"Number of valid overlapping pixels: {num_valid}")
                        
                        # Change Detection Logic
                        prob_map = None
                        if use_ai:
                            from .ai_change_detection import predict_change
                            print("Running AI inference on tile pair...")
                            prob_map = predict_change(data_b, data_a)
                            threshold = 0.5
                            mask = ((prob_map > threshold) & valid_mask).astype(np.uint8)
                        else:
                            # Calculate absolute difference safely on valid pixels
                            diff = np.zeros_like(data_b, dtype=np.float32)
                            diff[valid_mask] = np.abs(data_a[valid_mask].astype(np.float32) - data_b[valid_mask].astype(np.float32))
                            
                            # Apply a threshold (e.g., difference > 50 pixel value out of 255)
                            threshold = 50
                            mask = ((diff > threshold) & valid_mask).astype(np.uint8)
                        
                        num_changed = np.sum(mask)
                        print(f"Number of changed pixels (above threshold): {num_changed}")
                        
                        # Vectorize the mask
                        results = (
                            {'properties': {'raster_val': v}, 'geometry': s}
                            for i, (s, v) 
                            in enumerate(
                                shapes(mask, mask=mask, transform=src_b.transform)
                            )
                        )
                        
                        polygons = []
                        
                        transformer = None
                        if src_b.crs and src_b.crs.to_epsg() != 4326:
                            transformer = Transformer.from_crs(src_b.crs, "EPSG:4326", always_xy=True)
                            
                        for result in results:
                            geom = shape(result['geometry'])
                            
                            # Reproject from raster CRS to WGS84
                            wgs84_geom = self.reproject_geometry_to_wgs84(geom, transformer)
                            wgs84_geom = make_valid(wgs84_geom)
                            
                            # Noise filtering: Discard tiny artifacts
                            min_area_threshold = 0.00001
                            
                            if not wgs84_geom.is_empty and wgs84_geom.area > min_area_threshold:
                                polygons.append(wgs84_geom)
                                
                        print(f"Number of generated valid polygons: {len(polygons)}")
                                
                        if polygons:
                            for poly in polygons:
                                wkt_geom = f"SRID=4326;{poly.wkt}"
                                
                                if use_ai and prob_map is not None:
                                    # Calculate confidence as the average AI probability of the polygon
                                    # Create a raster mask for this specific polygon to get the mean probability
                                    geom_mask = geometry_mask([geom], out_shape=prob_map.shape, transform=src_b.transform, invert=True)
                                    poly_prob = float(np.mean(prob_map[geom_mask])) if np.sum(geom_mask) > 0 else 0.5
                                    confidence = poly_prob
                                    classification = "change"
                                else:
                                    confidence = base_confidence
                                    classification = "change"
                                    if base_confidence < 0.6:
                                        classification = "high_risk_false_alarm"
                                
                                detection = ChangeDetection(
                                    pair_id=pair.id,
                                    confidence=confidence,
                                    classification=classification,
                                    geom=wkt_geom
                                )
                                self.db.add(detection)
                                detections_made += 1
                                
                except Exception as e:
                    print(f"Error processing tile pair: {e}")
                finally:
                    if os.path.exists(b_path): os.remove(b_path)
                    if os.path.exists(a_path): os.remove(a_path)
                    if 'b_mask_path' in locals() and os.path.exists(b_mask_path): os.remove(b_mask_path)
                    if 'a_mask_path' in locals() and os.path.exists(a_mask_path): os.remove(a_mask_path)
                    
        self.db.commit()
        return {"status": "success", "detections_made": detections_made, "pair_id": pair_id}
