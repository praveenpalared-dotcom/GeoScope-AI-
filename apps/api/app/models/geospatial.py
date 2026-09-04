from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from pgvector.sqlalchemy import Vector
from .base import Base
import datetime

class AOI(Base):
    __tablename__ = 'aois'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    geom = Column(Geometry('POLYGON', srid=4326))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    __table_args__ = (Index('idx_aoi_geom', 'geom', postgresql_using='gist'),)

class SatelliteScene(Base):
    __tablename__ = 'satellite_scenes'
    id = Column(String, primary_key=True, index=True)
    acquisition_time = Column(DateTime)
    cloud_cover = Column(Float)
    platform = Column(String)  # e.g., Sentinel-2
    geom = Column(Geometry('POLYGON', srid=4326)) 
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tiles = relationship("SatelliteTile", back_populates="scene")
    __table_args__ = (Index('idx_scene_geom', 'geom', postgresql_using='gist'),)

class SatelliteTile(Base):
    __tablename__ = 'satellite_tiles'
    id = Column(String, primary_key=True, index=True)
    scene_id = Column(String, ForeignKey('satellite_scenes.id'))
    minio_path = Column(String)
    embedding = Column(Vector(512)) # Assuming 512-dim vector for embeddings
    geom = Column(Geometry('POLYGON', srid=4326))
    
    scene = relationship("SatelliteScene", back_populates="tiles")
    __table_args__ = (
        Index('idx_tile_geom', 'geom', postgresql_using='gist'),
        Index('idx_satellite_tile_embedding', 'embedding', 
              postgresql_using='hnsw', 
              postgresql_with={'m': 16, 'ef_construction': 64}, 
              postgresql_ops={'embedding': 'vector_cosine_ops'})
    )

class TemporalPair(Base):
    __tablename__ = 'temporal_pairs'
    id = Column(Integer, primary_key=True, index=True)
    before_scene_id = Column(String, ForeignKey('satellite_scenes.id'))
    after_scene_id = Column(String, ForeignKey('satellite_scenes.id'))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    before_scene = relationship("SatelliteScene", foreign_keys=[before_scene_id])
    after_scene = relationship("SatelliteScene", foreign_keys=[after_scene_id])
    detections = relationship("ChangeDetection", back_populates="pair")

class DetectionCluster(Base):
    __tablename__ = 'detection_clusters'
    id = Column(Integer, primary_key=True, index=True)
    geom = Column(Geometry('POLYGON', srid=4326))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    detections = relationship("ChangeDetection", back_populates="cluster")
    __table_args__ = (Index('idx_cluster_geom', 'geom', postgresql_using='gist'),)

class ChangeDetection(Base):
    __tablename__ = 'change_detections'
    id = Column(Integer, primary_key=True, index=True)
    pair_id = Column(Integer, ForeignKey('temporal_pairs.id'))
    cluster_id = Column(Integer, ForeignKey('detection_clusters.id'), nullable=True)
    confidence = Column(Float)
    classification = Column(String, default="unknown")
    status = Column(String, default="pending") # pending, confirmed, rejected, escalated
    geom = Column(Geometry('POLYGON', srid=4326))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    pair = relationship("TemporalPair", back_populates="detections")
    cluster = relationship("DetectionCluster", back_populates="detections")
    reviews = relationship("AnalystReview", back_populates="detection")
    
    __table_args__ = (Index('idx_detection_geom', 'geom', postgresql_using='gist'),)

class AnalystReview(Base):
    __tablename__ = 'analyst_reviews'
    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, ForeignKey('change_detections.id'))
    action = Column(String) # CONFIRM, REJECT, ESCALATE
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    detection = relationship("ChangeDetection", back_populates="reviews")
