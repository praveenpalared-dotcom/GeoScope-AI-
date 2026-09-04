from sentence_transformers import SentenceTransformer
from PIL import Image
import torch

class EmbeddingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        print("Loading CLIP model (this may take a minute on first run)...")
        # Use GPU if available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # clip-ViT-B-32 produces 512-d embeddings, which matches our pgvector configuration
        self.model = SentenceTransformer('clip-ViT-B-32', device=self.device)
        print(f"CLIP model loaded on {self.device}.")

    def get_text_embedding(self, text: str) -> list[float]:
        """Generate a 512-dimensional embedding for a text query."""
        # The model returns a numpy array. We convert to list of floats for pgvector.
        embedding = self.model.encode([text])[0]
        return embedding.tolist()

    def get_image_embedding(self, image: Image.Image) -> list[float]:
        """Generate a 512-dimensional embedding for a PIL Image."""
        # Convert to RGB just in case
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        embedding = self.model.encode([image])[0]
        return embedding.tolist()

# Singleton instance
embedding_service = EmbeddingService()
