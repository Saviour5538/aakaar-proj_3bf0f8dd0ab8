from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
from .ingest import ingest_excel
from .rag import answer_query

router = APIRouter(prefix='/api/ai')
logger = logging.getLogger(__name__)

class IngestRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    filename: Optional[str] = Field(None, description="Original filename")

class IngestResponse(BaseModel):
    success: bool
    message: str
    chunks_created: int = 0
    session_id: str
    error: Optional[str] = None

class QueryRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier for context")
    query: str = Field(..., description="User's natural language query")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")

class QueryResponse(BaseModel):
    success: bool
    answer: str
    session_id: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None

@router.post("/ingest", response_model=IngestResponse)
async def ingest(
    session_id: str,
    file: UploadFile = File(...)
):
    """
    Endpoint to upload and ingest an Excel file.
    Processes the file with overlapping chunking and stores in vector DB.
    """
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls)")

        logger.info(f"Ingesting file {file.filename} for session {session_id}")
        chunks_count = await ingest_excel(file, session_id)

        return IngestResponse(
            success=True,
            message=f"File {file.filename} ingested successfully",
            chunks_created=chunks_count,
            session_id=session_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingest error for session {session_id}: {e}", exc_info=True)
        return IngestResponse(
            success=False,
            message="Ingest failed",
            chunks_created=0,
            session_id=session_id,
            error=str(e)
        )

@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest
):
    """
    Endpoint to query the ingested data using agentic Graph RAG.
    """
    try:
        logger.info(f"Query received for session {request.session_id}: {request.query}")
        answer, sources = await answer_query(
            session_id=request.session_id,
            query=request.query,
            top_k=request.top_k
        )

        return QueryResponse(
            success=True,
            answer=answer,
            session_id=request.session_id,
            sources=sources
        )
    except Exception as e:
        logger.error(f"Query error for session {request.session_id}: {e}", exc_info=True)
        return QueryResponse(
            success=False,
            answer="",
            session_id=request.session_id,
            sources=[],
            error=str(e)
        )