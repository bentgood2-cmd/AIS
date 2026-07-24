import math

import pytest

torch = pytest.importorskip("torch")

from spectral_semantics.neural_lm import NeuralLM, SPECIAL_TOKENS, Vocab, train_neural_lm

_TINY_CORPUS = [
    "the cat sat on the mat".split(),
    "the dog sat on the rug".split(),
    "a cat and a dog are friends".split(),
    "the small cat likes the warm mat".split(),
    "the big dog likes the warm rug".split(),
] * 20  # repeat so min_count=1 training still has enough signal for a smoke test


@pytest.fixture(scope="module")
def tiny_lm() -> NeuralLM:
    model, vocab = train_neural_lm(
        sentences=_TINY_CORPUS, epochs=3, seq_len=8, batch_size=16,
        emb_dim=16, hidden_dim=32, verbose=False, save=False,
    )
    return NeuralLM(model, vocab)


def test_vocab_build_includes_special_tokens_and_words():
    vocab = Vocab.build(_TINY_CORPUS, min_count=1)
    for tok in SPECIAL_TOKENS:
        assert tok in vocab.word_to_id
    assert "cat" in vocab.word_to_id
    assert len(vocab) == len(vocab.id_to_word) == len(vocab.word_to_id)


def test_sentence_logprob_is_finite_and_negative(tiny_lm):
    lp = tiny_lm.sentence_logprob(["the", "cat", "sat", "on", "the", "mat"])
    assert math.isfinite(lp)
    assert lp < 0  # log-probabilities of a multi-token sequence are negative


def test_sentence_logprob_per_token_matches_manual_division(tiny_lm):
    tokens = ["the", "dog", "sat", "on", "the", "rug"]
    assert tiny_lm.sentence_logprob_per_token(tokens) == pytest.approx(
        tiny_lm.sentence_logprob(tokens) / len(tokens)
    )


def test_sentence_logprob_per_token_empty_is_zero(tiny_lm):
    assert tiny_lm.sentence_logprob_per_token([]) == 0.0


def test_topk_next_words_excludes_special_tokens_and_respects_k(tiny_lm):
    words = tiny_lm.topk_next_words(["the"], top_k=5)
    assert len(words) == 5
    assert all(w not in SPECIAL_TOKENS for w in words)


def test_topk_next_words_deterministic(tiny_lm):
    a = tiny_lm.topk_next_words(["the", "cat"], top_k=5)
    b = tiny_lm.topk_next_words(["the", "cat"], top_k=5)
    assert a == b


def test_unknown_word_does_not_crash(tiny_lm):
    lp = tiny_lm.sentence_logprob(["the", "zzznonexistentword", "sat"])
    assert math.isfinite(lp)


# ---- rewrite.py wiring ----

from spectral_semantics.embeddings import Embedder
from spectral_semantics.masks import persona_mask
from spectral_semantics.rewrite import candidate_words, guided_rewrite, neural_candidates
from spectral_semantics.spectral import bandpass_mask

SENTENCE = "the old man walked slowly across the quiet garden".split()


@pytest.fixture(scope="module")
def embedder():
    return Embedder()


def test_neural_candidates_returns_in_vocab_words(tiny_lm, embedder):
    # tiny_lm's own vocab is tiny and unrelated to SENTENCE, so just check
    # the plumbing: it returns *something* usable as embedder-filtered input.
    words = neural_candidates(SENTENCE, 1, tiny_lm, top_k=5)
    assert len(words) <= 5
    assert all(isinstance(w, str) for w in words)


def test_candidate_words_with_neural_lm_merges_without_duplicates(tiny_lm, embedder):
    p = 1  # "old"
    merged = candidate_words(SENTENCE, p, embedder, neural_lm=tiny_lm, max_neural=5)
    assert merged[0] == SENTENCE[p]
    assert len(merged) == len(set(merged))


def test_guided_rewrite_with_neural_lm_never_worse_than_noop(tiny_lm, embedder):
    from spectral_semantics.ngram_lm import get_lm

    lm = get_lm()
    L = len(SENTENCE)
    band = bandpass_mask(L, 2, L // 2 - 1)
    mask = persona_mask("urgent", L)
    result = guided_rewrite(
        SENTENCE, embedder, lm, mask, band, strength=0.8, beam_size=8,
        neural_lm=tiny_lm, use_neural_candidates=True, fluency_scorer=tiny_lm,
    )
    assert result.beam_trace[-1] <= result.beam_trace[0] + 1e-9


def test_guided_rewrite_fluency_scorer_defaults_to_lm(tiny_lm, embedder):
    """fluency_scorer=None should fall back to `lm`, not silently use something
    else -- this is what makes guided_rewrite's existing (pre-neural_lm)
    callers and tests keep working unchanged.
    """
    from spectral_semantics.ngram_lm import get_lm

    lm = get_lm()
    L = len(SENTENCE)
    band = bandpass_mask(L, 2, L // 2 - 1)
    mask = persona_mask("empathetic", L)
    result = guided_rewrite(SENTENCE, embedder, lm, mask, band, strength=0.5, beam_size=4)
    assert result.baseline_fluency_per_token == pytest.approx(lm.sentence_logprob_per_token(SENTENCE))
