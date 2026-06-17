import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from database.models import (
    Base, engine, SessionLocal, UserSession, UploadedFile, DocumentChunk,
    GraphNode, GraphEdge, UserQuery, SystemConfiguration
)

def seed_database():
    """Insert realistic sample data into all tables."""
    db = SessionLocal()
    try:
        print("Starting database seeding...")

        # Clear existing data (reverse order due to foreign keys)
        print("Clearing existing data...")
        db.query(SystemConfiguration).delete()
        db.query(UserQuery).delete()
        db.query(GraphEdge).delete()
        db.query(GraphNode).delete()
        db.query(DocumentChunk).delete()
        db.query(UploadedFile).delete()
        db.query(UserSession).delete()
        db.commit()

        # 1. UserSession (parent)
        print("Seeding UserSession...")
        sessions = [
            UserSession(
                session_id="session_001_abc123def456",
                created_at=datetime.utcnow() - timedelta(days=2),
                last_accessed=datetime.utcnow() - timedelta(hours=1),
                is_active=True,
                metadata={"user_agent": "Mozilla/5.0", "ip": "192.168.1.10"}
            ),
            UserSession(
                session_id="session_002_ghi789jkl012",
                created_at=datetime.utcnow() - timedelta(days=1),
                last_accessed=datetime.utcnow() - timedelta(minutes=30),
                is_active=True,
                metadata={"user_agent": "Chrome/120.0", "ip": "192.168.1.20"}
            ),
            UserSession(
                session_id="session_003_mno345pqr678",
                created_at=datetime.utcnow() - timedelta(hours=6),
                last_accessed=datetime.utcnow() - timedelta(minutes=5),
                is_active=False,
                metadata={"user_agent": "Safari/17.0", "ip": "192.168.1.30"}
            )
        ]
        db.add_all(sessions)
        db.commit()
        session_ids = [s.id for s in sessions]

        # 2. UploadedFile (child of UserSession)
        print("Seeding UploadedFile...")
        files = [
            UploadedFile(
                session_id=session_ids[0],
                original_filename="research_paper.pdf",
                stored_filename="upload_001_xyz789.pdf",
                file_size=2048576,
                mime_type="application/pdf",
                upload_status="processed",
                uploaded_at=datetime.utcnow() - timedelta(days=2, hours=3),
                processed_at=datetime.utcnow() - timedelta(days=2, hours=2),
                processing_errors=None,
                metadata={"pages": 12, "author": "Dr. Smith", "title": "AI Research"}
            ),
            UploadedFile(
                session_id=session_ids[0],
                original_filename="meeting_notes.txt",
                stored_filename="upload_002_abc456.txt",
                file_size=153600,
                mime_type="text/plain",
                upload_status="processed",
                uploaded_at=datetime.utcnow() - timedelta(days=1, hours=5),
                processed_at=datetime.utcnow() - timedelta(days=1, hours=4),
                processing_errors=None,
                metadata={"lines": 45, "meeting_date": "2024-01-15"}
            ),
            UploadedFile(
                session_id=session_ids[1],
                original_filename="presentation.pptx",
                stored_filename="upload_003_def123.pptx",
                file_size=5242880,
                mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                upload_status="pending",
                uploaded_at=datetime.utcnow() - timedelta(hours=2),
                processed_at=None,
                processing_errors="File too large for processing",
                metadata={"slides": 25, "topic": "Quarterly Review"}
            )
        ]
        db.add_all(files)
        db.commit()
        file_ids = [f.id for f in files]

        # 3. DocumentChunk (child of UploadedFile)
        print("Seeding DocumentChunk...")
        chunks = []
        chunk_texts = [
            "Artificial intelligence is transforming industries by enabling machines to learn from data.",
            "Machine learning algorithms can identify patterns and make predictions with high accuracy.",
            "Deep learning uses neural networks with multiple layers to model complex relationships.",
            "Natural language processing allows computers to understand and generate human language.",
            "Computer vision enables machines to interpret and analyze visual information from the world."
        ]
        for file_idx, file_id in enumerate(file_ids[:2]):  # Only first two files have chunks
            for chunk_idx in range(3):
                text = chunk_texts[(file_idx * 3 + chunk_idx) % len(chunk_texts)]
                chunk = DocumentChunk(
                    uploaded_file_id=file_id,
                    chunk_index=chunk_idx,
                    chunk_text=text,
                    chunk_size=len(text),
                    overlap_size=50 if chunk_idx > 0 else 0,
                    start_position=chunk_idx * 500,
                    end_position=chunk_idx * 500 + len(text),
                    embedding_vector=[0.1 * i for i in range(1536)],
                    created_at=datetime.utcnow() - timedelta(days=file_idx + 1)
                )
                chunks.append(chunk)
        db.add_all(chunks)
        db.commit()
        chunk_ids = [c.id for c in chunks]

        # 4. GraphNode (child of UploadedFile and DocumentChunk)
        print("Seeding GraphNode...")
        nodes = [
            GraphNode(
                node_id="node_001_concept_ai",
                node_type="concept",
                node_content="Artificial Intelligence",
                source_file_id=file_ids[0],
                source_chunk_id=chunk_ids[0],
                embedding_vector=[0.2 * i for i in range(1536)],
                metadata={"category": "technology", "importance": 0.9},
                created_at=datetime.utcnow() - timedelta(days=2)
            ),
            GraphNode(
                node_id="node_002_concept_ml",
                node_type="concept",
                node_content="Machine Learning",
                source_file_id=file_ids[0],
                source_chunk_id=chunk_ids[1],
                embedding_vector=[0.3 * i for i in range(1536)],
                metadata={"category": "technology", "importance": 0.8},
                created_at=datetime.utcnow() - timedelta(days=2)
            ),
            GraphNode(
                node_id="node_003_concept_nlp",
                node_type="concept",
                node_content="Natural Language Processing",
                source_file_id=file_ids[1],
                source_chunk_id=chunk_ids[3],
                embedding_vector=[0.4 * i for i in range(1536)],
                metadata={"category": "technology", "importance": 0.7},
                created_at=datetime.utcnow() - timedelta(days=1)
            ),
            GraphNode(
                node_id="node_004_entity_openai",
                node_type="entity",
                node_content="OpenAI",
                source_file_id=file_ids[0],
                source_chunk_id=None,
                embedding_vector=[0.5 * i for i in range(1536)],
                metadata={"type": "organization", "founded": 2015},
                created_at=datetime.utcnow() - timedelta(days=2)
            ),
            GraphNode(
                node_id="node_005_entity_researcher",
                node_type="entity",
                node_content="AI Researcher",
                source_file_id=file_ids[1],
                source_chunk_id=None,
                embedding_vector=[0.6 * i for i in range(1536)],
                metadata={"type": "profession", "skills": ["Python", "TensorFlow"]},
                created_at=datetime.utcnow() - timedelta(days=1)
            )
        ]
        db.add_all(nodes)
        db.commit()
        node_ids = [n.id for n in nodes]

        # 5. GraphEdge (child of GraphNode)
        print("Seeding GraphEdge...")
        edges = [
            GraphEdge(
                edge_id="edge_001_ai_ml",
                source_node_id=node_ids[0],
                target_node_id=node_ids[1],
                edge_type="subfield_of",
                weight=0.9,
                metadata={"confidence": 0.95, "source": "text_analysis"},
                created_at=datetime.utcnow() - timedelta(days=2)
            ),
            GraphEdge(
                edge_id="edge_002_ml_nlp",
                source_node_id=node_ids[1],
                target_node_id=node_ids[2],
                edge_type="includes",
                weight=0.8,
                metadata={"confidence": 0.88, "source": "text_analysis"},
                created_at=datetime.utcnow() - timedelta(days=2)
            ),
            GraphEdge(
                edge_id="edge_003_openai_ai",
                source_node_id=node_ids[3],
                target_node_id=node_ids[0],
                edge_type="researches",
                weight=0.7,
                metadata={"confidence": 0.92, "source": "knowledge_graph"},
                created_at=datetime.utcnow() - timedelta(days=2)
            ),
            GraphEdge(
                edge_id="edge_004_researcher_nlp",
                source_node_id=node_ids[4],
                target_node_id=node_ids[2],
                edge_type="works_on",
                weight=0.6,
                metadata={"confidence": 0.85, "source": "text_analysis"},
                created_at=datetime.utcnow() - timedelta(days=1)
            ),
            GraphEdge(
                edge_id="edge_005_ai_nlp",
                source_node_id=node_ids[0],
                target_node_id=node_ids[2],
                edge_type="enables",
                weight=0.75,
                metadata={"confidence": 0.80, "source": "text_analysis"},
                created_at=datetime.utcnow() - timedelta(days=1)
            )
        ]
        db.add_all(edges)
        db.commit()

        # 6. UserQuery (child of UserSession)
        print("Seeding UserQuery...")
        queries = [
            UserQuery(
                session_id=session_ids[0],
                query_text="What is artificial intelligence?",
                query_timestamp=datetime.utcnow() - timedelta(days=2, hours=1),
                response_text="Artificial intelligence is the simulation of human intelligence processes by machines, especially computer systems.",
                response_timestamp=datetime.utcnow() - timedelta(days=2, hours=1, minutes=2),
                processing_time_ms=1250,
                retrieved_node_ids=[node_ids[0], node_ids[1]],
                retrieved_chunk_ids=[chunk_ids[0], chunk_ids[1]],
                query_status="completed",
                error_message=None,
                metadata={"model": "gpt-4", "temperature": 0.7}
            ),
            UserQuery(
                session_id=session_ids[0],
                query_text="Explain machine learning algorithms",
                query_timestamp=datetime.utcnow() - timedelta(days=1, hours=2),
                response_text="Machine learning algorithms use statistical techniques to give computers the ability to learn from data without being explicitly programmed.",
                response_timestamp=datetime.utcnow() - timedelta(days=1, hours=2, minutes=3),
                processing_time_ms=1800,
                retrieved_node_ids=[node_ids[1], node_ids[2]],
                retrieved_chunk_ids=[chunk_ids[1], chunk_ids[2]],
                query_status="completed",
                error_message=None,
                metadata={"model": "gpt-4", "temperature": 0.7}
            ),
            UserQuery(
                session_id=session_ids[1],
                query_text="What companies work on AI?",
                query_timestamp=datetime.utcnow() - timedelta(hours=3),
                response_text=None,
                response_timestamp=None,
                processing_time_ms=None,
                retrieved_node_ids=[],
                retrieved_chunk_ids=[],
                query_status="failed",
                error_message="No relevant documents found in the knowledge graph",
                metadata={"model": "gpt-4", "temperature": 0.7}
            )
        ]
        db.add_all(queries)
        db.commit()

        # 7. SystemConfiguration
        print("Seeding SystemConfiguration...")
        configs = [
            SystemConfiguration(
                config_key="chunk_size",
                config_value="1000",
                config_type="integer",
                description="Size of document chunks in characters",
                updated_at=datetime.utcnow() - timedelta(days=10)
            ),
            SystemConfiguration(
                config_key="chunk_overlap",
                config_value="200",
                config_type="integer",
                description="Overlap between consecutive chunks in characters",
                updated_at=datetime.utcnow() - timedelta(days=10)
            ),
            SystemConfiguration(
                config_key="embedding_model",
                config_value="text-embedding-ada-002",
                config_type="string",
                description="Model used for generating embeddings",
                updated_at=datetime.utcnow() - timedelta(days=5)
            ),
            SystemConfiguration(
                config_key="similarity_threshold",
                config_value="0.75",
                config_type="float",
                description="Minimum similarity score for retrieval",
                updated_at=datetime.utcnow() - timedelta(days=3)
            ),
            SystemConfiguration(
                config_key="max_retrieved_nodes",
                config_value="10",
                config_type="integer",
                description="Maximum number of nodes to retrieve per query",
                updated_at=datetime.utcnow() - timedelta(days=1)
            )
        ]
        db.add_all(configs)
        db.commit()

        print("Database seeding completed successfully!")
        print(f"Inserted: {len(sessions)} sessions, {len(files)} files, {len(chunks)} chunks,")
        print(f"          {len(nodes)} nodes, {len(edges)} edges, {len(queries)} queries,")
        print(f"          {len(configs)} configurations")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    seed_database()