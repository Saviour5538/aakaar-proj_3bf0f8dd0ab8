from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import io
import uuid
import os
from datetime import datetime
from pydantic import BaseModel, Field
from database.config import get_db
from database.models import UploadedFile, SessionLog
from backend.auth.dependencies import get_current_user

router = APIRouter(prefix='/upload', tags=['Upload'])

# Pydantic schemas
class UploadedFileBase(BaseModel):
    filename: str
    file_size: int
    mime_type: str
    session_id: Optional[int] = None

class UploadedFileCreate(UploadedFileBase):
    pass

class UploadedFileResponse(UploadedFileBase):
    id: int
    created_at: datetime
    processed: bool
    chunk_count: Optional[int] = None

    class Config:
        from_attributes = True

class ChunkInfo(BaseModel):
    id: int
    content: str
    chunk_index: int
    overlap_percentage: float
    created_at: datetime

    class Config:
        from_attributes = True

class UploadedFileDetailResponse(UploadedFileResponse):
    chunks: List[ChunkInfo] = []

    class Config:
        from_attributes = True

@router.get("/", response_model=List[UploadedFileResponse])
def get_uploaded_files(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    files = db.query(UploadedFile).offset(skip).limit(limit).all()
    return files

@router.get("/{file_id}", response_model=UploadedFileDetailResponse)
def get_uploaded_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return file

@router.post("/", response_model=UploadedFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_excel_file(
    file: UploadFile = File(...),
    session_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only Excel or CSV files are allowed")
    
    # Read file content
    contents = await file.read()
    file_size = len(contents)
    
    # Validate session if provided
    if session_id:
        session = db.query(SessionLog).filter(SessionLog.id == session_id).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    # Create file record
    db_file = UploadedFile(
        filename=file.filename,
        file_size=file_size,
        mime_type=file.content_type,
        session_id=session_id,
        processed=False,
        chunk_count=0
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    # Process file for overlapping chunks (simplified - actual chunking would be async)
    try:
        # This would be moved to a background task in production
        df = pd.read_excel(io.BytesIO(contents)) if file.filename.endswith(('.xlsx', '.xls')) else pd.read_csv(io.BytesIO(contents))
        
        # Convert dataframe to text for chunking
        text_content = df.to_string(index=False)
        
        # Apply overlapping chunking (500 chars with 10% overlap)
        chunk_size = 500
        overlap = 50  # 10% of 500
        chunks = []
        
        for i in range(0, len(text_content), chunk_size - overlap):
            chunk = text_content[i:i + chunk_size]
            if chunk.strip():
                chunks.append(chunk)
        
        # Update file with chunk count
        db_file.chunk_count = len(chunks)
        db_file.processed = True
        db.commit()
        
    except Exception as e:
        db_file.processed = False
        db.commit()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"File processing failed: {str(e)}")
    
    return db_file

@router.put("/{file_id}", response_model=UploadedFileResponse)
def update_uploaded_file(
    file_id: int,
    file_update: UploadedFileCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    db_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    # Update fields
    for field, value in file_update.dict(exclude_unset=True).items():
        setattr(db_file, field, value)
    
    db.commit()
    db.refresh(db_file)
    return db_file

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_uploaded_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    db_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    db.delete(db_file)
    db.commit()
    return None