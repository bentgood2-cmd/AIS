"""
A local, honestly-small word embedding backend.

The source papers assume some pretrained encoding function Phi(T) without
saying what it is. This environment's network policy blocks fetching a
pretrained vector file (e.g. GloVe) from an arbitrary external host, so
instead of faking it, this module trains a real (if modest) Word2Vec model
on nltk's local Brown + Gutenberg corpora. The spectral math in spectral.py
is agnostic to where the (d, L) embedding matrix comes from — swapping in
a bigger pretrained model later would not require changing anything else.
"""
from __future__ import annotations

import os
from functools import lru_cache

import numpy as np
from gensim.models import Word2Vec

from .corpus import training_sentences

_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", ".cache")
_MODEL_PATH = os.path.join(_CACHE_DIR, "word2vec.model")


@lru_cache(maxsize=1)
def get_model(vector_size: int = 100, window: int = 5, min_count: int = 3) -> Word2Vec:
    os.makedirs(_CACHE_DIR, exist_ok=True)
    if os.path.exists(_MODEL_PATH):
        return Word2Vec.load(_MODEL_PATH)
    sents = training_sentences()
    model = Word2Vec(
        sentences=sents,
        vector_size=vector_size,
        window=window,
        min_count=min_count,
        workers=os.cpu_count() or 2,
        epochs=8,
        seed=0,
    )
    model.save(_MODEL_PATH)
    return model


class Embedder:
    """Wraps a trained Word2Vec model as Phi: tokens -> (d, L) matrix."""

    def __init__(self, model: Word2Vec | None = None):
        self.model = model or get_model()
        self.dim = self.model.vector_size
        # OOV fallback: mean of all vectors (a bland, near-origin point --
        # not ideal, but explicit and deterministic rather than crashing).
        self._oov_vector = self.model.wv.vectors.mean(axis=0)

    def in_vocab(self, word: str) -> bool:
        return word in self.model.wv

    def word_vector(self, word: str) -> np.ndarray:
        if word in self.model.wv:
            return self.model.wv[word]
        return self._oov_vector

    def encode(self, tokens: list[str]) -> np.ndarray:
        """tokens -> E in R^{d x L}."""
        if not tokens:
            raise ValueError("cannot encode an empty token sequence")
        return np.stack([self.word_vector(t) for t in tokens], axis=1)

    def most_similar_in_vocab(self, vector: np.ndarray, topn: int = 1, exclude: set[str] = frozenset()):
        return [
            w for w, _ in self.model.wv.similar_by_vector(vector, topn=topn + len(exclude))
            if w not in exclude
        ][:topn]
