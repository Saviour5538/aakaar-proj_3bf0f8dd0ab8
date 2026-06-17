from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from database.config import get_db
from database.models import RAGQuery, SessionLog, UploadedFile, DataChunk
from backend.auth.dependencies import get_current_user

router = APIRouter(prefix='/rag', tags=['RAG'])

# Pydantic schemas
class RAGQueryBase(BaseModel):
    session_id: Optional[int] = None
    query_text: str
    parameters: Optional[Dict[str, Any]] = None

class RAGQueryCreate(RAGQueryBase):
    pass

class RAGQueryResponse(RAGQueryBase):
    id: int
    created_at: datetime
    response_text: Optional[str] = None
    status: str
    processing_time_ms: Optional[int] = None
    chunk_ids_used: Optional[List[int]] = None

    class Config:
        from_attributes = True

class GraphNode(BaseModel):
    id: str
    label: str
    properties: Dict[str, Any]

class GraphEdge(BaseModel):
    source: str
    target: str
    label: str
    properties: Dict[str, Any]

class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class RAGQueryDetailResponse(RAGQueryResponse):
    graph_data: Optional[GraphResponse] = None
    source_chunks: List[DataChunk] = []

    class Config:
        from_attributes = True

@router.get("/queries", response_model=List[RAGQueryResponse])
def get_rag_queries(
    session_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(RAGQuery)
    if session_id:
        query = query.filter(RAGQuery.session_id == session_id)
    queries = query.order_by(RAGQuery.created_at.desc()).offset(skip).limit(limit).all()
    return queries

@router.get("/queries/{query_id}", response_model=RAGQueryDetailResponse)
def get_rag_query(
    query_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(RAGQuery).filter(RAGQuery.id == query_id).first()
    if not query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query not found")
    
    # Get source chunks if chunk_ids_used exists
    source_chunks = []
    if query.chunk_ids_used:
        source_chunks = db.query(DataChunk).filter(DataChunk.id.in_(query.chunk_ids_used)).all()
    
    response = RAGQueryDetailResponse(
        **query.__dict__,
        source_chunks=source_chunks,
        graph_data=None  # Would be populated from graph database in real implementation
    )
    return response

@router.post("/queries", response_model=RAGQueryResponse, status_code=status.HTTP_201_CREATED)
def create_rag_query(
    query_data: RAGQueryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Validate session if provided
    if query_data.session_id:
        session = db.query(SessionLog).filter(SessionLog.id == query_data.session_id).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    # Create query record
    db_query = RAGQuery(
        **query_data.dict(),
        status="pending",
        created_at=datetime.utcnow()
    )
    db.add(db_query)
    db.commit()
    db.refresh(db_query)
    
    # In a real implementation, this would trigger:
    # 1. Agentic RAG pipeline
    # 2. Graph retrieval
    # 3. Response generation
    
    # For now, simulate processing
    import time
    start_time = time.time()
    
    # Simulate RAG processing
    time.sleep(0.1)  # Simulate processing delay
    
    # Generate mock response
    db_query.response_text = f"Processed query: {query_data.query_text[:50]}..."
    db_query.status = "completed"
    db_query.processing_time_ms = int((time.time() - start_time) * 1000)
    db_query.chunk_ids_used = [1, 2, 3]  # Mock chunk IDs
    
    db.commit()
    db.refresh(db_query)
    
    return db_query

@router.put("/queries/{query_id}", response_model=RAGQueryResponse)
def update_rag_query(
    query_id: int,
    query_update: RAGQueryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    db_query = db.query(RAGQuery).filter(RAGQuery.id == query_id).first()
    if not db_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query not found")
    
    # Can only update pending queries
    if db_query.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update query with status: {db_query.status}"
        )
    
    # Update fields
    for field, value in query_update.dict(exclude_unset=True).items():
        setattr(db_query, field, value)
    
    db.commit()
    db.refresh(db_query)
    return db_query

@router.delete("/queries/{query_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rag_query(
    query_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    db_query = db.query(RAGQuery).filter(RAGQuery.id == query_id).first()
    if not db_query:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query not found")
    
    db.delete(db_query)
    db.commit()
    return None

@router.post("/graph/search", response_model=GraphResponse)
def search_graph(
    search_term: str,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # In a real implementation, this would query Neo4j or similar graph database
    # For now, return mock graph data
    
    mock_nodes = [
        GraphNode(id="1", label="Entity", properties={"name": "Customer", "type": "concept"}),
        GraphNode(id="2", label="Entity", properties={"name": "Order", "type": "concept"}),
        GraphNode(id="3", label="Instance", properties={"name": "John Doe", "type": "customer"}),
        GraphNode(id="4", label="Instance", properties={"name": "Order-123", "type": "order"}),
    ]
    
    mock_edges = [
        GraphEdge(source="1", target="2", label="HAS", properties={"relationship": "association"}),
        GraphEdge(source="3", target="4", label="PLACED", properties={"date": "2024-01-15"}),
        GraphEdge(source="3", target="1", label="INSTANCE_OF", properties={}),
        GraphEdge(source="4", target="2", label="INSTANCE_OF", properties={}),
    ]
    
    return GraphResponse(nodes=mock_nodes, edges=mock_edges)

@router.get("/sessions/{session_id}/graph", response_model=GraphResponse)
def get_session_graph(
    session_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Validate session exists
    session = db.query(SessionLog).filter(SessionLog.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    # In a real implementation, this would retrieve the knowledge graph
    # built from the session's uploaded files
    
    # Mock response
    mock_nodes = [
        GraphNode(id=str(session_id), label="Session", properties={"id": session_id, "status": session.status}),
        GraphNode(id="file_1", label="File", properties={"name": "sales_data.xlsx", "type": "excel"}),
        GraphNode(id="concept_1", label="Concept", properties={"name": "Revenue", "type": "metric"}),
    ]
    
    mock_edges = [
        GraphEdge(source=str(session_id), target="file_1", label="CONTAINS", properties={}),
        GraphEdge(source="file_1", target="concept_1", label="EXTRACTS", properties={"confidence": 0.85}),
    ]
    
    return GraphResponse(nodes=mock_nodes, edges=mock_edges)