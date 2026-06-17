import os
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    Float,
    JSON,
    Index,
    UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from sqlalchemy.sql import func

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    metadata = Column(JSON, default=dict)
    
    uploaded_files = relationship("UploadedFile", back_populates="session", cascade="all, delete-orphan")
    queries = relationship("UserQuery", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_user_sessions_created_at", "created_at"),
        Index("ix_user_sessions_is_active", "is_active"),
    )
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, session_id={self.session_id}, created_at={self.created_at})>"

class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("user_sessions.id", ondelete="CASCADE"), nullable=False)
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), unique=True, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    upload_status = Column(String(50), default="pending", nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    processing_errors = Column(Text, nullable=True)
    metadata = Column(JSON, default=dict)
    
    session = relationship("UserSession", back_populates="uploaded_files")
    chunks = relationship("DocumentChunk", back_populates="uploaded_file", cascade="all, delete-orphan")
    graph_nodes = relationship("GraphNode", back_populates="source_file", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_uploaded_files_session_id", "session_id"),
        Index("ix_uploaded_files_upload_status", "upload_status"),
        Index("ix_uploaded_files_uploaded_at", "uploaded_at"),
        Index("ix_uploaded_files_processed_at", "processed_at"),
    )
    
    def __repr__(self):
        return f"<UploadedFile(id={self.id}, original_filename={self.original_filename}, status={self.upload_status})>"

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    uploaded_file_id = Column(Integer, ForeignKey("uploaded_files.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_size = Column(Integer, nullable=False)
    overlap_size = Column(Integer, nullable=False)
    start_position = Column(Integer, nullable=False)
    end_position = Column(Integer, nullable=False)
    embedding_vector = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    uploaded_file = relationship("UploadedFile", back_populates="chunks")
    graph_nodes = relationship("GraphNode", back_populates="source_chunk", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_document_chunks_uploaded_file_id", "uploaded_file_id"),
        Index("ix_document_chunks_chunk_index", "chunk_index"),
        Index("ix_document_chunks_start_position", "start_position"),
        Index("ix_document_chunks_end_position", "end_position"),
        UniqueConstraint("uploaded_file_id", "chunk_index", name="uq_chunk_file_index"),
    )
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, file_id={self.uploaded_file_id}, index={self.chunk_index}, size={self.chunk_size})>"

class GraphNode(Base):
    __tablename__ = "graph_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(255), unique=True, nullable=False, index=True)
    node_type = Column(String(100), nullable=False)
    node_content = Column(Text, nullable=False)
    source_file_id = Column(Integer, ForeignKey("uploaded_files.id", ondelete="CASCADE"), nullable=True)
    source_chunk_id = Column(Integer, ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True)
    embedding_vector = Column(JSON, nullable=True)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    source_file = relationship("UploadedFile", back_populates="graph_nodes")
    source_chunk = relationship("DocumentChunk", back_populates="graph_nodes")
    outgoing_edges = relationship("GraphEdge", foreign_keys="[GraphEdge.source_node_id]", back_populates="source_node", cascade="all, delete-orphan")
    incoming_edges = relationship("GraphEdge", foreign_keys="[GraphEdge.target_node_id]", back_populates="target_node", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_graph_nodes_node_type", "node_type"),
        Index("ix_graph_nodes_source_file_id", "source_file_id"),
        Index("ix_graph_nodes_source_chunk_id", "source_chunk_id"),
        Index("ix_graph_nodes_created_at", "created_at"),
    )
    
    def __repr__(self):
        return f"<GraphNode(id={self.id}, node_id={self.node_id}, type={self.node_type})>"

class GraphEdge(Base):
    __tablename__ = "graph_edges"
    
    id = Column(Integer, primary_key=True, index=True)
    edge_id = Column(String(255), unique=True, nullable=False, index=True)
    source_node_id = Column(Integer, ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(Integer, ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False)
    edge_type = Column(String(100), nullable=False)
    weight = Column(Float, default=1.0, nullable=False)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    source_node = relationship("GraphNode", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node = relationship("GraphNode", foreign_keys=[target_node_id], back_populates="incoming_edges")
    
    __table_args__ = (
        Index("ix_graph_edges_source_node_id", "source_node_id"),
        Index("ix_graph_edges_target_node_id", "target_node_id"),
        Index("ix_graph_edges_edge_type", "edge_type"),
        Index("ix_graph_edges_weight", "weight"),
        UniqueConstraint("source_node_id", "target_node_id", "edge_type", name="uq_edge_source_target_type"),
    )
    
    def __repr__(self):
        return f"<GraphEdge(id={self.id}, edge_id={self.edge_id}, source={self.source_node_id}, target={self.target_node_id})>"

class UserQuery(Base):
    __tablename__ = "user_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("user_sessions.id", ondelete="CASCADE"), nullable=False)
    query_text = Column(Text, nullable=False)
    query_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    response_text = Column(Text, nullable=True)
    response_timestamp = Column(DateTime, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    retrieved_node_ids = Column(JSON, default=list)
    retrieved_chunk_ids = Column(JSON, default=list)
    query_status = Column(String(50), default="pending", nullable=False)
    error_message = Column(Text, nullable=True)
    metadata = Column(JSON, default=dict)
    
    session = relationship("UserSession", back_populates="queries")
    
    __table_args__ = (
        Index("ix_user_queries_session_id", "session_id"),
        Index("ix_user_queries_query_timestamp", "query_timestamp"),
        Index("ix_user_queries_query_status", "query_status"),
    )
    
    def __repr__(self):
        return f"<UserQuery(id={self.id}, session_id={self.session_id}, status={self.query_status})>"

class SystemConfiguration(Base):
    __tablename__ = "system_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(255), unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=False)
    config_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index("ix_system_configurations_config_type", "config_type"),
    )
    
    def __repr__(self):
        return f"<SystemConfiguration(id={self.id}, key={self.config_key}, type={self.config_type})>"

def create_tables():
    Base.metadata.create_all(bind=engine)

def drop_tables():
    Base.metadata.drop_all(bind=engine)