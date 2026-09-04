from sqlalchemy.orm import Session
from sqlalchemy import text
from ..models.geospatial import ChangeDetection, DetectionCluster

class DiscoveryService:
    def __init__(self, db: Session):
        self.db = db
        
    def generate_spatial_clusters(self, eps: float = 0.01, min_points: int = 2):
        """
        Group unclustered detections into spatial hotspots using PostGIS ST_ClusterDBSCAN.
        eps is the distance threshold (in degrees for WGS84, e.g. 0.01 ~ 1km).
        """
        # We find all unclustered detections first
        unclustered_query = "SELECT id, geom FROM change_detections WHERE cluster_id IS NULL"
        
        # We can run DBSCAN over all unclustered points.
        # ST_ClusterDBSCAN returns a cluster ID for each geometry.
        sql = text(f"""
            WITH clusters AS (
                SELECT 
                    id, 
                    ST_ClusterDBSCAN(geom, eps := :eps, minpoints := :min_points) over () as cid
                FROM change_detections
                WHERE cluster_id IS NULL
            ),
            cluster_hulls AS (
                SELECT 
                    cid, 
                    ST_ConvexHull(ST_Collect(c.geom)) as hull_geom,
                    array_agg(c.id) as detection_ids
                FROM clusters c JOIN change_detections cd ON c.id = cd.id
                WHERE cid IS NOT NULL
                GROUP BY cid
            )
            SELECT cid, hull_geom, detection_ids FROM cluster_hulls;
        """)
        
        result = self.db.execute(sql, {"eps": eps, "min_points": min_points}).fetchall()
        
        clusters_created = 0
        for row in result:
            cid, hull_geom, detection_ids = row
            
            # Create the new cluster record
            # We need to format the WKB/WKT correctly. We can just use text interpolation or ST_AsText if needed,
            # but SQLAlchemy execute returns string/hex for PostGIS geometry usually, or we can wrap it in ST_AsText in query.
            # Let's fix the query to return WKT:
            pass
            
        # Re-running with ST_AsText for simpler parsing
        sql_wkt = text(f"""
            WITH clusters AS (
                SELECT 
                    id, 
                    ST_ClusterDBSCAN(geom, eps := :eps, minpoints := :min_points) over () as cid
                FROM change_detections
                WHERE cluster_id IS NULL
            ),
            cluster_hulls AS (
                SELECT 
                    cid, 
                    ST_AsText(ST_ConvexHull(ST_Collect(cd.geom))) as hull_geom,
                    array_agg(c.id) as detection_ids
                FROM clusters c JOIN change_detections cd ON c.id = cd.id
                WHERE cid IS NOT NULL
                GROUP BY cid
            )
            SELECT cid, hull_geom, detection_ids FROM cluster_hulls;
        """)
        
        result = self.db.execute(sql_wkt, {"eps": eps, "min_points": min_points}).fetchall()
        
        for row in result:
            cid, hull_geom, detection_ids = row
            
            wkt = f"SRID=4326;{hull_geom}"
            cluster = DetectionCluster(geom=wkt)
            self.db.add(cluster)
            self.db.flush() # Get cluster ID
            
            # Update the corresponding detections
            self.db.query(ChangeDetection).filter(
                ChangeDetection.id.in_(detection_ids)
            ).update({"cluster_id": cluster.id}, synchronize_session=False)
            
            clusters_created += 1
            
        self.db.commit()
        return {"status": "success", "clusters_created": clusters_created}
