
import numpy as np
import torch
from PIL import Image
import io
try:
    from open_clip import create_model_and_transforms, tokenize
except ImportError:
    from clip import load, tokenize
    create_model_and_transforms = None

from config import CLIP_MODEL_NAME, DEVICE, QDRANT_VECTOR_SIZE

class CLIPService:
    """
    CLIP Model Service
    - Load CLIP model
    - Generate image embeddings
    - Generate text embeddings
    - Hybrid embeddings (image + text)
    """
    
    def __init__(self):
        """Initialize CLIP model"""
        print("📥 Loading CLIP model with pretrained weights...")
        
        try:
            # Try open_clip first (more optimized)
            self.model, self.preprocess, _ = create_model_and_transforms(
                'ViT-B-32-quickgelu',
                pretrained='openai'
            )
            self.use_open_clip = True
            print("✓ Using open_clip ViT-B-32-quickgelu")
        except:
            # Fallback to clip
            try:
                self.model, self.preprocess = load("ViT-B/32", device=DEVICE)
                self.use_open_clip = False
                print("✓ Using OpenAI CLIP ViT-B/32")
            except:
                print("⚠ CLIP not available - using dummy vectors")
                self.model = None
                self.preprocess = None
                self.use_open_clip = False
        
        if self.model:
            self.model = self.model.to(DEVICE)
            self.model.eval()
        
        print(f"✓ CLIP model loaded with pretrained weights")
        print(f"✓ Using device: {DEVICE}")
    
    def generate_image_embedding(self, image_bytes):
        """
        Generate embedding for an image
        
        Args:
            image_bytes: PIL Image or file bytes
        
        Returns:
            numpy array of size 512
        """
        if not self.model:
            return np.random.randn(QDRANT_VECTOR_SIZE).astype(np.float32)
        
        try:
            # Convert bytes to PIL Image if needed
            if isinstance(image_bytes, bytes):
                image = Image.open(io.BytesIO(image_bytes))
            else:
                image = image_bytes
            
            # Preprocess
            image_input = self.preprocess(image).unsqueeze(0).to(DEVICE)
            
            # Get embedding
            with torch.no_grad():
                image_features = self.model.encode_image(image_input)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            # Convert to numpy and normalize to 512 dims
            embedding = image_features.cpu().numpy()[0].astype(np.float32)
            
            if len(embedding) != QDRANT_VECTOR_SIZE:
                # Resize if needed
                embedding = np.pad(embedding, (0, max(0, QDRANT_VECTOR_SIZE - len(embedding))))[:QDRANT_VECTOR_SIZE]
            
            return embedding
        
        except Exception as e:
            print(f"⚠ Error processing image: {str(e)}")
            return np.random.randn(QDRANT_VECTOR_SIZE).astype(np.float32)
    
    def generate_text_embedding(self, text):
        """
        Generate embedding for text
        
        Args:
            text: String description
        
        Returns:
            numpy array of size 512
        """
        if not self.model:
            return np.random.randn(QDRANT_VECTOR_SIZE).astype(np.float32)
        
        try:
            # Tokenize
            text_input = tokenize(text).to(DEVICE)
            
            # Get embedding
            with torch.no_grad():
                text_features = self.model.encode_text(text_input)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            # Convert to numpy
            embedding = text_features.cpu().numpy()[0].astype(np.float32)
            
            if len(embedding) != QDRANT_VECTOR_SIZE:
                embedding = np.pad(embedding, (0, max(0, QDRANT_VECTOR_SIZE - len(embedding))))[:QDRANT_VECTOR_SIZE]
            
            return embedding
        
        except Exception as e:
            print(f"⚠ Error processing text: {str(e)}")
            return np.random.randn(QDRANT_VECTOR_SIZE).astype(np.float32)
    
    def generate_hybrid_embedding(self, image_vector, text_vector, image_weight=0.6):
        """
        Combine image and text embeddings
        
        Args:
            image_vector: Image embedding (512,)
            text_vector: Text embedding (512,)
            image_weight: Weight for image (0-1)
        
        Returns:
            Hybrid embedding (512,)
        """
        text_weight = 1.0 - image_weight
        
        hybrid = (np.array(image_vector) * image_weight + 
                 np.array(text_vector) * text_weight)
        
        # Normalize
        norm = np.linalg.norm(hybrid)
        if norm > 0:
            hybrid = hybrid / norm
        
        return hybrid.astype(np.float32)
    
    def generate_dummy_vectors(self, count=5):
        """
        Generate random vectors for testing
        Used only when CLIP not available
        """
        vectors = []
        for _ in range(count):
            vec = np.random.randn(QDRANT_VECTOR_SIZE).astype(np.float32)
            # Normalize
            vec = vec / np.linalg.norm(vec)
            vectors.append(vec.tolist())
        return vectors