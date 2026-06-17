import os
from typing import List
import openai
from openai import OpenAI

class EmbeddingClient:
    """Client for embedding text using the pinned embedding model."""
    def __init__(self):
        self._client = None
        self.model = "text-embedding-3-small"
        self.dimensions = 1536

    @property
    def client(self):
        """Lazy initialization of OpenAI client using environment variable."""
        if self._client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self._client = OpenAI(api_key=api_key)
        return self._client

    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string."""
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
            dimensions=self.dimensions
        )
        return response.data[0].embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of text strings."""
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
            dimensions=self.dimensions
        )
        return [item.embedding for item in response.data]

def get_embedding(texts: List[str]) -> List[List[float]]:
    """Module-level function to create client and embed batch of texts."""
    client = EmbeddingClient()
    return client.embed_batch(texts)