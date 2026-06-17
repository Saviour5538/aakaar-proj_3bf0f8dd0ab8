import os
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import Json
import numpy as np

class PgVectorStore:
    """Vector store implementation using pgvector."""
    def __init__(self):
        self._connection = None
        self.embedding_dim = 1536

    @property
    def connection(self):
        """Lazy initialization of PostgreSQL connection."""
        if self._connection is None:
            conn_str = os.getenv("PGVECTOR_CONNECTION_STRING")
            if not conn_str:
                raise ValueError("PGVECTOR_CONNECTION_STRING environment variable not set")
            self._connection = psycopg2.connect(conn_str)
            self._connection.autocommit = True
            self._ensure_vector_extension()
            self._ensure_table()
        return self._connection

    def _ensure_vector_extension(self):
        """Ensure the vector extension is enabled."""
        with self.connection.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    def _ensure_table(self):
        """Ensure the embeddings table exists with correct schema."""
        with self.connection.cursor() as cur:
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id TEXT PRIMARY KEY,
                    embedding vector({self.embedding_dim}),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # Create index for similarity search
            cur.execute("""
                CREATE INDEX IF NOT EXISTS embedding_idx 
                ON embeddings USING ivfflat (embedding vector_cosine_ops);
            """)

    def upsert(self, id: str, vector: List[float], metadata: Dict[str, Any]):
        """Insert or update a vector with metadata."""
        with self.connection.cursor() as cur:
            cur.execute("""
                INSERT INTO embeddings (id, embedding, metadata)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) 
                DO UPDATE SET 
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata,
                    created_at = CURRENT_TIMESTAMP;
            """, (id, np.array(vector).tolist(), Json(metadata)))

    def search(self, query_embedding: List[float], top_k: int = 5, **filters) -> List[Dict[str, Any]]:
        """Search for similar vectors with optional metadata filters."""
        # Build WHERE clause from filters
        where_clauses = []
        params = [np.array(query_embedding).tolist(), top_k]
        
        for key, value in filters.items():
            where_clauses.append(f"metadata->>%s = %s")
            params.extend([key, str(value)])
        
        where_sql = " AND ".join(where_clauses)
        if where_sql:
            where_sql = "WHERE " + where_sql
        
        query = f"""
            SELECT id, embedding, metadata, 
                   1 - (embedding <=> %s) as similarity
            FROM embeddings
            {where_sql}
            ORDER BY embedding <=> %s
            LIMIT %s;
        """
        
        with self.connection.cursor() as cur:
            cur.execute(query, params)
            results = cur.fetchall()
            
        return [
            {
                "id": row[0],
                "embedding": row[1],
                "metadata": row[2],
                "similarity": float(row[3])
            }
            for row in results
        ]

    def close(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None