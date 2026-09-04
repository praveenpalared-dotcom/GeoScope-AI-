import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import rasterio
from PIL import Image
from app.services.minio_client import minio_client

router = APIRouter(prefix="/tiles", tags=["tiles"])

@router.get("/{scene_id}/{tile_id}.png")
def get_tile_image(scene_id: str, tile_id: str):
    """
    Stream a specific pre-processed COG tile from MinIO directly as a PNG image.
    This serves as our lightweight MVP raster endpoint.
    """
    bucket = "geoscope"
    minio_path = f"tiles/{scene_id}/{tile_id}.tif"
    temp_path = f"/tmp/{tile_id}_serving.tif"
    
    try:
        # 1. Fetch the raw TIF from MinIO
        try:
            minio_client.fget_object(bucket, minio_path, temp_path)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Tile not found: {e}")
            
        # 2. Open with rasterio to read data
        with rasterio.open(temp_path) as src:
            # We assume it has at least 1 band. Real multispectral needs RGB mapping.
            # For MVP, we'll take the first band and make it grayscale, or take 3 bands for RGB if they exist.
            
            if src.count >= 3:
                r = src.read(1)
                g = src.read(2)
                b = src.read(3)
                # Simple normalization to 0-255
                r = ((r - r.min()) / (r.max() - r.min() + 1e-5) * 255).astype('uint8')
                g = ((g - g.min()) / (g.max() - g.min() + 1e-5) * 255).astype('uint8')
                b = ((b - b.min()) / (b.max() - b.min() + 1e-5) * 255).astype('uint8')
                
                import numpy as np
                rgb = np.dstack((r, g, b))
                img = Image.fromarray(rgb)
            else:
                data = src.read(1)
                # Normalize
                data = ((data - data.min()) / (data.max() - data.min() + 1e-5) * 255).astype('uint8')
                img = Image.fromarray(data, mode='L')
                
        # 3. Save to a byte stream as PNG
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # 4. Stream back to client
        return StreamingResponse(img_byte_arr, media_type="image/png")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        import os
        if os.path.exists(temp_path):
            os.remove(temp_path)
