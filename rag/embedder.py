import logging

from fastembed import TextEmbedding
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)

# ONNX-based equivalent of all-MiniLM-L6-v2 — same embedding quality,
# no torch/transformers dependency, far lower memory footprint.
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model: TextEmbedding | None = None


def _get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)
    return _model


class FastEmbedEmbeddings(Embeddings):
    """Wraps fastembed so it's a drop-in replacement for HuggingFaceEmbeddings
    wherever langchain/FAISS expects an `Embeddings` object."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        model = _get_model()
        return [vec.tolist() for vec in model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        model = _get_model()
        return next(model.embed([text])).tolist()


def get_embedding_model() -> FastEmbedEmbeddings:
    return FastEmbedEmbeddings()