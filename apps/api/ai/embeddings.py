import hashlib
import json
import math
import re
import urllib.error
import urllib.request
from django.conf import settings
from .providers import ProviderError

class MockEmbeddingProvider:
    """Stable local feature vectors for development, not semantic-quality embeddings."""
    name = "mock-hash-v1"
    model_name = "mock-hash-v1"
    dimensions = 1536
    def embed_many(self, texts):
        vectors = []
        for text in texts:
            vector = [0.0] * self.dimensions
            tokens = re.findall(r"[a-z0-9]+", text.lower())
            for token in tokens:
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "big") % self.dimensions
                vector[index] += 1.0 if digest[4] & 1 else -1.0
            norm = math.sqrt(sum(value * value for value in vector))
            vectors.append([value / norm for value in vector] if norm else vector)
        return vectors

class OpenAIEmbeddingProvider:
    name = "openai"
    def __init__(self):
        self.api_key = settings.EMBEDDING_API_KEY or settings.AI_API_KEY
        self.base_url = settings.EMBEDDING_API_BASE_URL.rstrip("/")
        self.model = settings.EMBEDDING_MODEL
        endpoint_fingerprint = hashlib.sha256(self.base_url.encode("utf-8")).hexdigest()[:12]
        self.model_name = f"{self.model}:{endpoint_fingerprint}"
        self.dimensions = settings.EMBEDDING_DIMENSIONS
        if self.dimensions != 1536:
            raise ProviderError("The evidence vector column is configured for 1536 dimensions.")
        if not self.api_key: raise ProviderError("The embedding provider is missing its API key.")

    def embed_many(self, texts):
        if not texts: return []
        body = {"model": self.model, "input": [text[:6000] for text in texts], "encoding_format": "float", "dimensions": self.dimensions}
        request = urllib.request.Request(f"{self.base_url}/embeddings", data=json.dumps(body).encode(), headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=settings.AI_TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read(8_000_000).decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            raise ProviderError("The embedding provider request failed. Check provider settings and retry.") from exc
        vectors = [item.get("embedding", []) for item in sorted(payload.get("data", []), key=lambda item: item.get("index", 0))]
        if len(vectors) != len(texts) or any(len(vector) != self.dimensions for vector in vectors):
            raise ProviderError("The embedding provider returned vectors with an unexpected shape.")
        return vectors

def get_embedding_provider():
    provider = settings.EMBEDDING_PROVIDER.lower()
    if provider == "mock": return MockEmbeddingProvider()
    if provider in {"openai", "openai_compatible"}: return OpenAIEmbeddingProvider()
    raise ProviderError("The configured embedding provider is not supported by this application build.")
