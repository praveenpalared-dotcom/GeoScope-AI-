import sys
import os
import random
from datetime import datetime, timedelta
import numpy as np

# Add the parent directory to sys.path so we can import 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal, engine
from app.models.geospatial import SatelliteScene, SatelliteTile, DetectionCluster, ChangeDetection, TemporalPair
from app.services.minio_client import minio_client

def seed_db():
    db = SessionLocal()
    
    # Check if already seeded
    if db.query(SatelliteScene).first():
        print("Database already contains scenes. Skipping seed.")
        return

    print("Seeding database...")
    
    # 1. Create Scenes
    scenes = []
    base_date = datetime.utcnow() - timedelta(days=30)
    for i in range(20):
        # Create a polygon near some random coordinate
        lat, lon = random.uniform(30.0, 45.0), random.uniform(-120.0, -70.0)
        geom_wkt = f"POLYGON(({lon} {lat}, {lon+0.1} {lat}, {lon+0.1} {lat+0.1}, {lon} {lat+0.1}, {lon} {lat}))"
        
        scene = SatelliteScene(
            id=f"SCENE_{i:04d}",
            acquisition_time=base_date + timedelta(days=i, hours=random.randint(1, 12)),
            cloud_cover=random.uniform(0.0, 20.0),
            platform=random.choice(["Sentinel-2", "Landsat-9", "PlanetScope"]),
            geom=f"SRID=4326;{geom_wkt}"
        )
        scenes.append(scene)
        db.add(scene)
    
    db.commit()
    
    # 2. Create Tiles with Embeddings
    print("Seeding tiles and embeddings...")
    for scene in scenes:
        # Create 5 tiles per scene
        for j in range(5):
            embedding = np.random.rand(512).astype(np.float32)
            # Normalize it
            embedding = embedding / np.linalg.norm(embedding)
            
            tile = SatelliteTile(
                id=f"TILE_{scene.id}_{j}",
                scene_id=scene.id,
                minio_path=f"tiles/{scene.id}/tile_{j}.png",
                embedding=embedding.tolist(),
                geom=scene.geom # Roughly same geom for simplicity
            )
            db.add(tile)
    db.commit()

    # 3. Create Temporal Pairs and Change Detections
    print("Seeding detections...")
    # Create some clusters first
    clusters = []
    for c in range(5):
        lat, lon = random.uniform(30.0, 45.0), random.uniform(-120.0, -70.0)
        geom_wkt = f"POLYGON(({lon} {lat}, {lon+0.01} {lat}, {lon+0.01} {lat+0.01}, {lon} {lat+0.01}, {lon} {lat}))"
        cluster = DetectionCluster(geom=f"SRID=4326;{geom_wkt}")
        db.add(cluster)
        clusters.append(cluster)
    db.commit()

    for i in range(10):
        pair = TemporalPair(
            before_scene_id=scenes[i].id,
            after_scene_id=scenes[i+10].id
        )
        db.add(pair)
        db.commit()
        
        # Add 1-3 detections per pair
        for _ in range(random.randint(1, 3)):
            cluster = random.choice(clusters)
            detection = ChangeDetection(
                pair_id=pair.id,
                cluster_id=cluster.id,
                confidence=random.uniform(0.7, 0.99),
                classification=random.choice(["construction", "deforestation", "vehicle_movement", "damage"]),
                status=random.choice(["pending", "pending", "confirmed", "rejected"]),
                geom=cluster.geom
            )
            db.add(detection)
    
    db.commit()

    print("Database seeded successfully!")

    # 4. Ensure MinIO buckets exist
    try:
        if not minio_client.bucket_exists("geoscope-tiles"):
            minio_client.make_bucket("geoscope-tiles")
            print("Created MinIO bucket: geoscope-tiles")
    except Exception as e:
        print(f"Warning: Could not create MinIO bucket: {e}")

if __name__ == "__main__":
    seed_db()
