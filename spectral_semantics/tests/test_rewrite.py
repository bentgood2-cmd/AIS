import numpy as np
import pytest

from spectral_semantics.embeddings import Embedder
from spectral_semantics.masks import persona_mask
from spectral_semantics.ngram_lm import get_lm
from spectral_semantics.rewrite import (
    content_positions,
    guided_rewrite,
    synonym_candidates,
)
from spectral_semantics.spectral import bandpass_mask


@pytest.fixture(scope="module")
def embedder():
    return Embedder()


@pytest.fixture(scope="module")
def lm():
    return get_lm()


SENTENCE = "the old man walked slowly across the quiet garden".split()


def test_synonym_candidates_always_include_original_first(embedder):
    positions = content_positions(SENTENCE)
    assert positions, "expected at least one content word in the test sentence"
    for p in positions:
        cands = synonym_candidates(SENTENCE, p, embedder)
        assert cands[0] == SENTENCE[p]
        assert len(cands) == len(set(cands)), "candidates should be deduplicated"


def test_synonym_candidates_deterministic_across_calls(embedder):
    p = content_positions(SENTENCE)[0]
    c1 = synonym_candidates(SENTENCE, p, embedder)
    c2 = synonym_candidates(SENTENCE, p, embedder)
    assert c1 == c2


def test_guided_rewrite_never_worse_than_noop(embedder, lm):
    L = len(SENTENCE)
    band = bandpass_mask(L, 2, L // 2 - 1)
    for kind in ["empathetic", "urgent"]:
        mask = persona_mask(kind, L)
        result = guided_rewrite(SENTENCE, embedder, lm, mask, band, strength=0.8, beam_size=8)
        # The search must never end up further from the target than doing
        # nothing at all -- "no substitution" is always a valid candidate at
        # every position, so the optimum can only be <= the no-op distance.
        assert result.beam_trace[-1] <= result.beam_trace[0] + 1e-9


def test_guided_rewrite_reproducible(embedder, lm):
    L = len(SENTENCE)
    band = bandpass_mask(L, 2, L // 2 - 1)
    mask = persona_mask("urgent", L)
    r1 = guided_rewrite(SENTENCE, embedder, lm, mask, band, strength=0.8, beam_size=8)
    r2 = guided_rewrite(SENTENCE, embedder, lm, mask, band, strength=0.8, beam_size=8)
    assert r1.tokens == r2.tokens
    assert r1.band_distance == pytest.approx(r2.band_distance)


def test_guided_rewrite_zero_strength_is_near_noop(embedder, lm):
    """At strength=0 the spectral target equals the original embedding, so
    the achievable distance should collapse close to zero (an exact 0 isn't
    guaranteed since substituting a word can only move through the discrete,
    finite set of WordNet synonym vectors, not land exactly back on the
    original point unless the search picks 'no substitution' everywhere).
    """
    L = len(SENTENCE)
    band = bandpass_mask(L, 2, L // 2 - 1)
    mask = persona_mask("urgent", L)
    result = guided_rewrite(SENTENCE, embedder, lm, mask, band, strength=0.0, beam_size=8)
    assert result.tokens == SENTENCE
    assert result.band_distance < 1e-6


def test_different_personas_produce_different_rewrites(embedder, lm):
    L = len(SENTENCE)
    band = bandpass_mask(L, 2, L // 2 - 1)
    r_emp = guided_rewrite(SENTENCE, embedder, lm, persona_mask("empathetic", L), band, strength=0.9, beam_size=8)
    r_urg = guided_rewrite(SENTENCE, embedder, lm, persona_mask("urgent", L), band, strength=0.9, beam_size=8)
    assert r_emp.tokens != r_urg.tokens
