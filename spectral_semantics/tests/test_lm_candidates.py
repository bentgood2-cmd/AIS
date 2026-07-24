import pytest

from spectral_semantics.embeddings import Embedder
from spectral_semantics.masks import persona_mask
from spectral_semantics.ngram_lm import get_lm
from spectral_semantics.rewrite import (
    candidate_words,
    content_positions,
    guided_rewrite,
    lm_proposal_candidates,
)
from spectral_semantics.spectral import bandpass_mask

SENTENCE = "the old man walked slowly across the quiet garden".split()


@pytest.fixture(scope="module")
def embedder():
    return Embedder()


@pytest.fixture(scope="module")
def lm():
    return get_lm()


def test_lm_proposal_candidates_deterministic_and_in_vocab(embedder, lm):
    c1 = lm_proposal_candidates(SENTENCE, 1, lm, embedder, top_k=10)
    c2 = lm_proposal_candidates(SENTENCE, 1, lm, embedder, top_k=10)
    assert c1 == c2
    assert len(c1) == 10
    assert all(embedder.in_vocab(w) for w in c1)


def test_lm_proposal_candidates_not_restricted_to_synonyms(embedder, lm):
    """The whole point of this candidate source: it should surface words
    that are NOT close synonyms of the original, unlike synonym_candidates.
    """
    from spectral_semantics.rewrite import synonym_candidates

    wn_cands = set(synonym_candidates(SENTENCE, 1, embedder))
    lm_cands = set(lm_proposal_candidates(SENTENCE, 1, lm, embedder, top_k=12))
    assert lm_cands - wn_cands, "expected at least some LM-proposed words outside the WordNet synonym set"


def test_candidate_words_merges_and_dedupes(embedder, lm):
    p = content_positions(SENTENCE)[0]
    merged = candidate_words(SENTENCE, p, embedder, lm=lm, max_wordnet=6, max_lm=10)
    assert merged[0] == SENTENCE[p]
    assert len(merged) == len(set(merged))
    without_lm = candidate_words(SENTENCE, p, embedder, lm=None)
    assert without_lm == candidate_words(SENTENCE, p, embedder)  # lm=None is the default


def test_guided_rewrite_with_lm_candidates_never_worse_than_noop(embedder, lm):
    """Same safety invariant as the WordNet-only decoder: 'no substitution'
    must always be reachable, regardless of candidate source.
    """
    L = len(SENTENCE)
    band = bandpass_mask(L, 2, L // 2 - 1)
    mask = persona_mask("urgent", L)
    result = guided_rewrite(
        SENTENCE, embedder, lm, mask, band, strength=0.8, beam_size=8, use_lm_candidates=True
    )
    assert result.beam_trace[-1] <= result.beam_trace[0] + 1e-9


def test_lm_candidates_reach_closer_to_target_than_wordnet_only(embedder, lm):
    """The empirical finding this module exists to test: relaxing beyond
    WordNet synonyms should let the search close more of the distance to
    the spectral target, since synonym sets are embedding-space-local by
    construction and cap how far any single substitution can move things.
    """
    L = len(SENTENCE)
    band = bandpass_mask(L, 2, L // 2 - 1)
    mask = persona_mask("urgent", L)
    wn_only = guided_rewrite(SENTENCE, embedder, lm, mask, band, strength=0.8, beam_size=8, use_lm_candidates=False)
    with_lm = guided_rewrite(SENTENCE, embedder, lm, mask, band, strength=0.8, beam_size=8, use_lm_candidates=True)
    assert with_lm.band_distance <= wn_only.band_distance
