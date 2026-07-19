"""
Local, offline text corpus + tokenization helpers.

Everything here comes from nltk's bundled Brown and Gutenberg corpora
(downloaded once via nltk.download in setup — no internet access needed at
run time, and in particular no dependency on an external pretrained
embedding file, since attempts to fetch one (e.g. GloVe via gensim's
downloader) were blocked by this environment's network policy).
"""
from __future__ import annotations

import re
from functools import lru_cache

import nltk


_TOKEN_RE = re.compile(r"^[a-zA-Z]+$")


def _clean_tokens(tokens: list[str]) -> list[str]:
    return [t.lower() for t in tokens if _TOKEN_RE.match(t)]


@lru_cache(maxsize=1)
def training_sentences(limit: int = 30000) -> list[list[str]]:
    """Tokenized, lowercased sentences (letters-only tokens) used to train
    both the word embedding and the fluency language model.
    """
    from nltk.corpus import brown, gutenberg

    sents: list[list[str]] = []
    for s in brown.sents():
        cleaned = _clean_tokens(s)
        if len(cleaned) >= 3:
            sents.append(cleaned)
        if len(sents) >= limit:
            return sents
    for s in gutenberg.sents():
        cleaned = _clean_tokens(s)
        if len(cleaned) >= 3:
            sents.append(cleaned)
        if len(sents) >= limit:
            break
    return sents


@lru_cache(maxsize=1)
def eval_sentences(n: int = 40, min_len: int = 7, max_len: int = 14) -> list[list[str]]:
    """A held-out-ish sample of real, moderate-length declarative sentences
    from Gutenberg, used as the base sentences for the feasibility
    experiments (watermarking / persona rewriting are applied to these).
    """
    from nltk.corpus import gutenberg

    out: list[list[str]] = []
    seen = set()
    for s in gutenberg.sents("austen-emma.txt"):
        cleaned = _clean_tokens(s)
        if not (min_len <= len(cleaned) <= max_len):
            continue
        key = tuple(cleaned)
        if key in seen:
            continue
        seen.add(key)
        out.append(cleaned)
        if len(out) >= n:
            break
    return out
