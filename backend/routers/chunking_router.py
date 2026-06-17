from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from database.config import get_db
from database.models import DataChunk, UploadedFile
from backend.auth.dependencies import get_current_user

router = APIRouter(prefix='/chunks', tags=['Chunking'])

# Pydantic schemas
class ChunkBase(BaseModel):
    file_id: int
    content: str
    chunk_index: int
    overlap_percentage: float = Field(ge=0, le=100)

class ChunkCreate(ChunkBase):
    pass

class ChunkResponse(ChunkBase):
    id: int
    created_at: datetime
    token_count: Optional[int] = None

    class Config:
        from_attributes = True

class ChunkingConfig(BaseModel):
    chunk_size: int = Field(default=500, ge=100, le=5000)
    overlap_percentage: float = Field(default=10.0, ge=0, le=50.0)
    delimiter: Optional[str] = None

@router.get("/", response_model=List[ChunkResponse])
def get_chunks(
    file_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(DataChunk)
    if file_id:
        query = query.filter(DataChunk.file_id == file_id)
    chunks = query.order_by(DataChunk.chunk_index).offset(skip).limit(limit).all()
    return chunks

@router.get("/{chunk_id}", response_model=ChunkResponse)
def get_chunk(
    chunk_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    chunk = db.query(DataChunk).filter(DataChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
    return chunk

@router.post("/", response_model=ChunkResponse, status_code=status.HTTP_201_CREATED)
def create_chunk(
    chunk_data: ChunkCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Verify file exists
    file = db.query(UploadedFile).filter(UploadedFile.id == chunk_data.file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    # Check for duplicate chunk index
    existing = db.query(DataChunk).filter(
        DataChunk.file_id == chunk_data.file_id,
        DataChunk.chunk_index == chunk_data.chunk_index
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chunk with index {chunk_data.chunk_index} already exists for this file"
        )
    
    db_chunk = DataChunk(**chunk_data.dict())
    db.add(db_chunk)
    db.commit()
    db.refresh(db_chunk)
    return db_chunk

@router.post("/process/{file_id}", response_model=List[ChunkResponse])
def process_file_chunks(
    file_id: int,
    config: ChunkingConfig,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Get file
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    # Check if file is already processed
    existing_chunks = db.query(DataChunk).filter(DataChunk.file_id == file_id).count()
    if existing_chunks > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File already has {existing_chunks} chunks. Delete existing chunks first."
        )
    
    # In a real implementation, this would:
    # 1. Load the file content
    # 2. Apply overlapping chunking algorithm
    # 3. Create chunk records
    
    # For now, return empty list as placeholder
    # Actual implementation would create chunks based on file content
    chunks = []
    
    # Update file chunk count
    file.chunk_count = len(chunks)
    file.processed = True
    db.commit()
    
    return chunks

@router.put("/{chunk_id}", response_model=ChunkResponse)
def update_chunk(
    chunk_id: int,
    chunk_update: ChunkCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    db_chunk = db.query(DataChunk).filter(DataChunk.id == chunk_id).first()
    if not db_chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
    
    # Check if updating file_id
    if chunk_update.file_id != db_chunk.file_id:
        new_file = db.query(UploadedFile).filter(UploadedFile.id == chunk_update.file_id).first()
        if not new_file:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New file not found")
    
    # Check for duplicate chunk index if changing
    if chunk_update.chunk_index != db_chunk.chunk_index:
        existing = db.query(DataChunk).filter(
            DataChunk.file_id == chunk_update.file_id,
            DataChunk.chunk_index == chunk_update.chunk_index
        ).first()
        if existing and existing.id != chunk_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Chunk with index {chunk_update.chunk_index} already exists for this file"
            )
    
    # Update fields
    for field, value in chunk_update.dict(exclude_unset=True).items():
        setattr(db_chunk, field, value)
    
    db.commit()
    db.refresh(db_chunk)
    return db_chunk

@router.delete("/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chunk(
    chunk_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    db_chunk = db.query(DataChunk).filter(DataChunk.id == chunk_id).first()
    if not db_chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chunk not found")
    
    # Update file chunk count
    file = db.query(UploadedFile).filter(UploadedFile.id == db_chunk.file_id).first()
    if file and file.chunk_count > 0:
        file.chunk_count -= 1
    
    db.delete(db_chunk)
    db.commit()
    return None