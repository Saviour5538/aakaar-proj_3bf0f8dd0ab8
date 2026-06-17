import os
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime

# Lazy imports
_vector_store = None
_embedding_fn = None
_llm_client = None

def _get_vector_store():
    """Lazy initialization of vector store."""
    global _vector_store
    if _vector_store is None:
        from pgvector.psycopg2 import register_vector
        import psycopg2
        from psycopg2.extras import Json
        
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
        from .embeddings import get_embedding
        _embedding_fn = get_embedding
    return _embedding_fn

def _get_llm_client():
    """Lazy initialization of LLM client."""
    global _llm_client
    if _llm_client is None:
        # Read API key from environment INSIDE function
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # Import here to avoid loading at module level
        from openai import OpenAI
        _llm_client = OpenAI(api_key=api_key)
    return _llm_client

def retrieve_context(query: str, top_k: int = 5, session_id: str = None, user_id: str = None) -> List[Dict[str, Any]]:
    """
    Retrieve relevant context using vector similarity and graph traversal.
    
    Args:
        query: User query
        top_k: Number of initial chunks to retrieve
        session_id: Session identifier
        user_id: User identifier
    
    Returns:
        List of relevant chunks with metadata
    """
    # Get embedding function
    get_embedding = _get_embedding_fn()
    
    # Embed the query
    query_embedding = get_embedding(query)
    query_embedding_array = np.array(query_embedding, dtype=np.float32)
    
    # Get vector store connection
    conn = _get_vector_store()
    cursor = conn.cursor()
    
    try:
        # Initial vector similarity search
        cursor.execute("""
            SELECT id, text, metadata, 
                   embedding <=> %s as distance
            FROM document_chunks
            WHERE session_id = %s AND user_id = %s
            ORDER BY embedding <=> %s
            LIMIT %s
        """, (query_embedding_array, session_id, user_id, query_embedding_array, top_k))
        
        initial_results = cursor.fetchall()
        
        if not initial_results:
            return []
        
        # Collect chunk IDs and retrieve graph-connected chunks
        chunk_ids = [row[0] for row in initial_results]
        all_chunks = []
        chunk_id_set = set(chunk_ids)
        
        # Get the initial chunks
        for row in initial_results:
            chunk_id, text, metadata, distance = row
            all_chunks.append({
                "id": chunk_id,
                "text": text,
                "metadata": metadata,
                "distance": float(distance),
                "source": "vector_search"
            })
        
        # Graph traversal: find related chunks through entities
        placeholders = ','.join(['%s'] * len(chunk_ids))
        query_params = chunk_ids + [session_id]
        
        cursor.execute(f"""
            SELECT DISTINCT dc.id, dc.text, dc.metadata, 
                   dc.embedding <=> %s as distance
            FROM document_chunks dc
            JOIN chunk_entity_relationships cer1 ON dc.id = cer1.chunk_id
            JOIN chunk_entity_relationships cer2 ON cer1.entity_name = cer2.entity_name
            WHERE cer2.chunk_id IN ({placeholders})
            AND dc.session_id = %s
            AND dc.id NOT IN ({placeholders})
            ORDER BY dc.embedding <=> %s
            LIMIT %s
        """, [query_embedding_array] + query_params + chunk_ids + [query_embedding_array, top_k])
        
        graph_results = cursor.fetchall()
        
        # Add graph-connected chunks
        for row in graph_results:
            chunk_id, text, metadata, distance = row
            if chunk_id not in chunk_id_set:
                all_chunks.append({
                    "id": chunk_id,
                    "text": text,
                    "metadata": metadata,
                    "distance": float(distance),
                    "source": "graph_traversal"
                })
                chunk_id_set.add(chunk_id)
        
        # Sort by distance and remove duplicates
        unique_chunks = {}
        for chunk in all_chunks:
            if chunk["id"] not in unique_chunks:
                unique_chunks[chunk["id"]] = chunk
            elif chunk["distance"] < unique_chunks[chunk["id"]]["distance"]:
                unique_chunks[chunk["id"]] = chunk
        
        # Return sorted results
        sorted_chunks = sorted(unique_chunks.values(), key=lambda x: x["distance"])
        return sorted_chunks[:top_k * 2]  # Return up to 2x top_k chunks
        
    except Exception as e:
        raise Exception(f"Error retrieving context: {str(e)}")
    finally:
        cursor.close()

def build_prompt(query: str, context_chunks: List[Dict[str, Any]]) -> str:
    """
    Build a prompt for the LLM using retrieved context.
    
    Args:
        query: User query
        context_chunks: Retrieved context chunks
    
    Returns:
        Formatted prompt string
    """
    if not context_chunks:
        return f"""You are an AI assistant. Answer the following question based on your general knowledge.

Question: {query}

Answer:"""
    
    # Format context
    context_text = ""
    for i, chunk in enumerate(context_chunks, 1):
        metadata = chunk.get("metadata", {})
        sheet = metadata.get("sheet_name", "Unknown")
        column = metadata.get("column_name", "Unknown")
        row = metadata.get("row", "Unknown")
        
        context_text += f"[Source {i} - Sheet: {sheet}, Column: {column}, Row: {row}]\n"
        context_text += f"{chunk['text']}\n\n"
    
    prompt = f"""You are an AI assistant analyzing data from Excel files. Use the provided context to answer the question.

Context from Excel data:
{context_text}

Question: {query}

Instructions:
1. Answer based ONLY on the provided context
2. If the context doesn't contain relevant information, say "I cannot find this information in the uploaded data"
3. Be precise and concise
4. Reference specific sources when possible (e.g., "According to Sheet X, Column Y...")

Answer:"""
    
    return prompt

def answer_question(query: str, session_id: str, user_id: str) -> Dict[str, Any]:
    """
    Main RAG function to answer questions.
    
    Args:
        query: User question
        session_id: Session identifier
        user_id: User identifier
    
    Returns:
        Dictionary with answer and sources
    """
    try:
        # Retrieve context
        context_chunks = retrieve_context(query, top_k=5, session_id=session_id, user_id=user_id)
        
        # Build prompt
        prompt = build_prompt(query, context_chunks)
        
        # Get LLM client
        llm_client = _get_llm_client()
        
        # Call LLM
        response = llm_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful data analysis assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Format sources
        sources = []
        for chunk in context_chunks:
            metadata = chunk.get("metadata", {})
            sources.append({
                "text_preview": chunk["text"][:100] + ("..." if len(chunk["text"]) > 100 else ""),
                "sheet": metadata.get("sheet_name", "Unknown"),
                "column": metadata.get("column_name", "Unknown"),
                "row": metadata.get("row", "Unknown"),
                "similarity_score": 1.0 - chunk.get("distance", 1.0)  # Convert distance to similarity
            })
        
        return {
            "answer": answer,
            "sources": sources,
            "query": query,
            "session_id": session_id,
            "context_chunks_count": len(context_chunks)
        }
    
    except Exception as e:
        return {
            "answer": f"Error: {str(e)}",
            "sources": [],
            "query": query,
            "session_id": session_id,
            "error": str(e)
        }