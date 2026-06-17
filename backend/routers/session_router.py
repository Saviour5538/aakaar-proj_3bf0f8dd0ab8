from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from database.config import get_db
from database.models import SessionLog, UploadedFile
from backend.auth.dependencies import get_current_user

router = APIRouter(prefix='/sessions', tags=['Sessions'])

# Pydantic schemas
class SessionBase(BaseModel):
    user_id: Optional[int] = None
    status: str = "active"
    metadata: Optional[dict] = None

class SessionCreate(SessionBase):
    pass

class SessionResponse(SessionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    file_count: int = 0

    class Config:
        from_attributes = True

class SessionDetailResponse(SessionResponse):
    files: List[UploadedFile] = []

    class Config:
        from_attributes = True

@router.get("/", response_model=List[SessionResponse])
def get_sessions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(SessionLog)
    if status:
        query = query.filter(SessionLog.status == status)
    sessions = query.offset(skip).limit(limit).all()
    
    # Add file count to each session
    for session in sessions:
        session.file_count = db.query(UploadedFile).filter(UploadedFile.session_id == session.id).count()
    
    return sessions

@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    session = db.query(SessionLog).filter(SessionLog.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    # Get associated files
    session.files = db.query(UploadedFile).filter(UploadedFile.session_id == session_id).all()
    session.file_count = len(session.files)
    
    return session

@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    db_session = SessionLog(**session_data.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    # Initialize file count
    db_session.file_count = 0
    
    return db_session

@router.put("/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: int,
    session_update: SessionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    db_session = db.query(SessionLog).filter(SessionLog.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    # Update fields
    for field, value in session_update.dict(exclude_unset=True).items():
        setattr(db_session, field, value)
    
    db_session.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_session)
    
    # Add file count
    db_session.file_count = db.query(UploadedFile).filter(UploadedFile.session_id == session_id).count()
    
    return db_session

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    db_session = db.query(SessionLog).filter(SessionLog.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    
    # Check if session has files
    file_count = db.query(UploadedFile).filter(UploadedFile.session_id == session_id).count()
    if file_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete session with {file_count} associated files"
        )
    
    db.delete(db_session)
    db.commit()
    return None