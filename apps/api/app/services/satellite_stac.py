from pathlib import Path
from datetime import datetime
import tempfile

import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds, reproject, Resampling
from pystac_client import Client


STAC_URL = "https://earth-search.aws.element84.com/v1"
COLLECTION = "sentinel-2-c1-l2a"


class SatelliteSTACService:

    def __init__(self):
        self.catalog = Client.open(STAC_URL)

    def search_scenes(
        self,
        bbox: list[float],
        start_date: str,
        end_date: str,
        max_cloud_cover: float = 20.0,
        limit: int = 10,
    ):
        search = self.catalog.search(
            collections=[COLLECTION],
            bbox=bbox,
            datetime=f"{start_date}/{end_date}",
            query={
                "eo:cloud_cover": {
                    "lt": max_cloud_cover
                }
            },
            max_items=limit,
        )

        items = list(search.items())

        items.sort(
            key=lambda item: item.properties.get(
                "eo:cloud_cover",
                100.0
            )
        )

        results = []

        for item in items:
            results.append({
                "id": item.id,
                "datetime": item.properties.get("datetime"),
                "cloud_cover": item.properties.get(
                    "eo:cloud_cover"
                ),
                "platform": item.properties.get(
                    "platform",
                    "Sentinel-2"
                ),
                "assets": {
                    key: asset.href
                    for key, asset in item.assets.items()
                    if asset.href
                },
            })

        return results

    def download_rgb(
        self,
        item_id: str,
        bbox: list[float],
        output_path: str,
    ):
        search = self.catalog.search(
            collections=[COLLECTION],
            ids=[item_id],
            max_items=1,
        )

        items = list(search.items())

        if not items:
            raise ValueError(
                f"Sentinel-2 scene not found: {item_id}"
            )

        item = items[0]

        assets = item.assets

        # Earth Search Sentinel-2 COG assets.
        band_keys = {
            "red": "red",
            "green": "green",
            "blue": "blue",
            "scl": "scl"
        }

        for name, key in band_keys.items():
            if key not in assets:
                raise RuntimeError(
                    f"Required RGB asset '{key}' not found. "
                    f"Available assets: {list(assets.keys())}"
                )

        red_href = assets["red"].href
        green_href = assets["green"].href
        blue_href = assets["blue"].href
        scl_href = assets["scl"].href

        with rasterio.open(red_href) as red_src:

            # Convert requested WGS84 bbox into
            # the satellite raster CRS.
            raster_bbox = transform_bounds(
                "EPSG:4326",
                red_src.crs,
                *bbox,
            )

            window = from_bounds(
                *raster_bbox,
                transform=red_src.transform,
            )

            window = window.round_offsets().round_lengths()

            red = red_src.read(
                1,
                window=window,
                boundless=True,
            )

            with rasterio.open(green_href) as green_src:
                green = green_src.read(
                    1,
                    window=window,
                    boundless=True,
                )

            with rasterio.open(blue_href) as blue_src:
                blue = blue_src.read(
                    1,
                    window=window,
                    boundless=True,
                )

            # Stack RGB.
            rgb = np.stack([
                red,
                green,
                blue,
            ])

            # Sentinel-2 reflectance is generally stored
            # at scaled integer values.
            rgb = rgb.astype(np.float32)

            # Percentile normalization for visualization.
            for i in range(3):
                band = rgb[i]

                low = np.percentile(
                    band,
                    2
                )

                high = np.percentile(
                    band,
                    98
                )

                if high > low:
                    band = (
                        (band - low)
                        / (high - low)
                        * 255.0
                    )

                rgb[i] = np.clip(
                    band,
                    0,
                    255
                )

            rgb = rgb.astype(np.uint8)

            profile = red_src.profile.copy()

            profile.update({
                "driver": "GTiff",
                "height": rgb.shape[1],
                "width": rgb.shape[2],
                "count": 3,
                "dtype": "uint8",
                "transform": rasterio.windows.transform(
                    window,
                    red_src.transform,
                ),
                "compress": "deflate",
                "tiled": True,
            })

            Path(output_path).parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with rasterio.open(
                output_path,
                "w",
                **profile,
            ) as dst:
                dst.write(rgb)

                dst.update_tags(
                    PLATFORM="Sentinel-2",
                    ACQUISITION_TIME=str(
                        item.properties.get("datetime", "")
                    ),
                    CLOUD_COVER=str(
                        item.properties.get(
                            "eo:cloud_cover",
                            ""
                        )
                    ),
                    STAC_ITEM_ID=item.id,
                )
                
            # Now handle SCL mask
            mask_output_path = output_path.replace('.tif', '_mask.tif')
            with rasterio.open(scl_href) as scl_src:
                scl_aligned = np.empty((rgb.shape[1], rgb.shape[2]), dtype=np.uint8)
                
                reproject(
                    source=rasterio.band(scl_src, 1),
                    destination=scl_aligned,
                    src_transform=scl_src.transform,
                    src_crs=scl_src.crs,
                    dst_transform=rasterio.windows.transform(window, red_src.transform),
                    dst_crs=red_src.crs,
                    resampling=Resampling.nearest
                )
                
                mask_profile = profile.copy()
                mask_profile.update({
                    "count": 1,
                    "dtype": "uint8"
                })
                
                with rasterio.open(mask_output_path, "w", **mask_profile) as mask_dst:
                    mask_dst.write(scl_aligned, 1)

        return {
            "status": "success",
            "item_id": item.id,
            "output_path": output_path,
            "mask_output_path": mask_output_path,
            "cloud_cover": item.properties.get(
                "eo:cloud_cover"
            ),
            "acquisition_time": item.properties.get(
                "datetime"
            ),
        }


satellite_stac_service = SatelliteSTACService()