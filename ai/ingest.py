import os
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import uuid
from datetime import datetime

# Lazy imports for vector store and embeddings
_vector_store = None
_embedding_fn = None

def _get_vector_store():
    """Lazy initialization of vector store."""
    global _vector_store
    if _vector_store is None:
        # Import here to avoid loading at module level
        from pgvector.psycopg2 import register_vector
        import psycopg2
        from psycopg2.extras import Json
        
        # Read connection details from environment
        db_host = os.getenv("PGVECTOR_HOST", "localhost")
        db_port = os.getenv("PGVECTOR_PORT", "5432")
        db_name = os.getenv("PGVECTOR_DATABASE", "ragdb")
        db_user = os.getenv("PGVECTOR_USER", "postgres")
        db_password = os.getenv("PGVECTOR_PASSWORD", "")
        
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        register_vector(conn)
        _vector_store = conn
    return _vector_store

def _get_embedding_fn():
    """Lazy import of embedding function."""
    global _embedding_fn
    if _embedding_fn is None:
        # Import here to avoid loading at module level
        from .embeddings import get_embedding
        _embedding_fn = get_embedding
    return _embedding_fn

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Input text to chunk
        chunk_size: Size of each chunk in characters
        chunk_overlap: Overlap between chunks in characters
    
    Returns:
        List of text chunks
    """
    if not text or len(text.strip()) == 0:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        
        # Ensure we don't cut in the middle of a word if possible
        if end < text_length:
            # Try to find the last space or newline
            last_space = text.rfind(' ', start, end)
            last_newline = text.rfind('\n', start, end)
            last_break = max(last_space, last_newline)
            
            if last_break > start and (end - last_break) < 100:  # Don't move too far back
                end = last_break + 1  # Include the space/newline
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position for next chunk
        start = end - chunk_overlap
        if start < 0:
            start = 0
        # Prevent infinite loop
        if start >= end:
            start = end
    
    return chunks

def process_excel_to_chunks(file_path: str) -> List[Dict[str, Any]]:
    """
    Read Excel file and convert each cell to chunks.
    
    Args:
        file_path: Path to Excel file
    
    Returns:
        List of chunk dictionaries with metadata
    """
    try:
        # Read all sheets
        excel_file = pd.ExcelFile(file_path)
        chunks = []
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # Process each cell
            for row_idx, row in df.iterrows():
                for col_idx, value in enumerate(row):
                    if pd.isna(value):
                        continue
                    
                    # Convert to string
                    cell_text = str(value).strip()
                    if not cell_text:
                        continue
                    
                    # Chunk the cell text
                    cell_chunks = chunk_text(cell_text, chunk_size=1000, chunk_overlap=200)
                    
                    for chunk_idx, chunk_text_content in enumerate(cell_chunks):
                        chunk_data = {
                            "id": str(uuid.uuid4()),
                            "text": chunk_text_content,
                            "metadata": {
                                "sheet_name": sheet_name,
                                "row": int(row_idx),
                                "column": int(col_idx),
                                "column_name": df.columns[col_idx] if col_idx < len(df.columns) else f"col_{col_idx}",
                                "chunk_index": chunk_idx,
                                "total_chunks": len(cell_chunks),
                                "file_path": file_path,
                                "cell_value_preview": cell_text[:100] + ("..." if len(cell_text) > 100 else "")
                            }
                        }
                        chunks.append(chunk_data)
        
        return chunks
    
    except Exception as e:
        raise Exception(f"Error processing Excel file: {str(e)}")

def embed_and_store_chunks(chunks: List[Dict[str, Any]], session_id: str, user_id: str):
    """
    Embed chunks and store in vector database.
    
    Args:
        chunks: List of chunk dictionaries
        session_id: Session identifier
        user_id: User identifier
    """
    if not chunks:
        return
    
    # Get embedding function
    get_embedding = _get_embedding_fn()
    
    # Get vector store connection
    conn = _get_vector_store()
    cursor = conn.cursor()
    
    try:
        # Prepare data for insertion
        for chunk in chunks:
            # Generate embedding
            embedding = get_embedding(chunk["text"])
            
            # Convert to numpy array for pgvector
            embedding_array = np.array(embedding, dtype=np.float32)
            
            # Insert into database
            cursor.execute("""
                INSERT INTO document_chunks 
                (id, text, embedding, metadata, session_id, user_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                text = EXCLUDED.text,
                embedding = EXCLUDED.embedding,
                metadata = EXCLUDED.metadata,
                updated_at = CURRENT_TIMESTAMP
            """, (
                chunk["id"],
                chunk["text"],
                embedding_array,
                chunk["metadata"],
                session_id,
                user_id,
                datetime.utcnow()
            ))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise Exception(f"Error storing chunks in database: {str(e)}")
    finally:
        cursor.close()

def ingest_excel(file_path: str, session_id: str, user_id: str) -> Dict[str, Any]:
    """
    Main ingestion function for Excel files.
    
    Args:
        file_path: Path to Excel file
        session_id: Session identifier
        user_id: User identifier
    
    Returns:
        Dictionary with ingestion results
    """
    try:
        # Process Excel file to chunks
        chunks = process_excel_to_chunks(file_path)
        
        # Store chunks in database
        embed_and_store_chunks(chunks, session_id, user_id)
        
        # Create entity graph nodes (simplified - in production would use NLP entity extraction)
        # For now, we'll create simple entity relationships based on sheet names and column names
        conn = _get_vector_store()
        cursor = conn.cursor()
        
        try:
            # Extract unique entities from metadata
            entities = set()
            for chunk in chunks:
                metadata = chunk["metadata"]
                entities.add(f"sheet:{metadata['sheet_name']}")
                entities.add(f"column:{metadata['column_name']}")
            
            # Store entities in graph table
            for entity in entities:
                cursor.execute("""
                    INSERT INTO entities (name, type, session_id, user_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (name, session_id) DO NOTHING
                """, (
                    entity,
                    entity.split(":")[0],
                    session_id,
                    user_id
                ))
            
            # Create relationships between chunks and entities
            for chunk in chunks:
                metadata = chunk["metadata"]
                sheet_entity = f"sheet:{metadata['sheet_name']}"
                column_entity = f"column:{metadata['column_name']}"
                
                # Link chunk to sheet entity
                cursor.execute("""
                    INSERT INTO chunk_entity_relationships 
                    (chunk_id, entity_name, relationship_type, session_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (chunk["id"], sheet_entity, "belongs_to", session_id))
                
                # Link chunk to column entity
                cursor.execute("""
                    INSERT INTO chunk_entity_relationships 
                    (chunk_id, entity_name, relationship_type, session_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (chunk["id"], column_entity, "from_column", session_id))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            # Don't fail ingestion if graph creation fails
            print(f"Warning: Graph creation failed: {str(e)}")
        finally:
            cursor.close()
        
        return {
            "status": "success",
            "chunks_processed": len(chunks),
            "session_id": session_id,
            "user_id": user_id,
            "file_path": file_path
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "session_id": session_id,
            "user_id": user_id
        }