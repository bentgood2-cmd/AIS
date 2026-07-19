import numpy as np
import pytest

from spectral_semantics.corpus import eval_paragraphs
from spectral_semantics.evaluation import roughness


def test_eval_paragraphs_length_bounds():
    paras = eval_paragraphs(n=5, min_words=50, max_words=100)
    assert len(paras) == 5
    for p in paras:
        assert 50 <= len(p) <= 100
        assert all(isinstance(w, str) and w.isalpha() for w in p)


def test_eval_paragraphs_deterministic():
    a = eval_paragraphs(n=3, min_words=50, max_words=100)
    b = eval_paragraphs(n=3, min_words=50, max_words=100)
    assert a == b


def test_roughness_zero_for_constant_trajectory():
    E = np.tile(np.array([[1.0], [2.0], [3.0]]), (1, 10))  # constant across time
    assert roughness(E) == pytest.approx(0.0, abs=1e-9)


def test_roughness_higher_for_alternating_than_smooth():
    t = np.linspace(0, 4 * np.pi, 40)
    smooth = np.sin(t / 8)[None, :]  # slow, smooth oscillation
    spiky = np.array([1.0 if i % 2 == 0 else -1.0 for i in range(40)])[None, :]
    assert roughness(spiky) > roughness(smooth)


def test_roughness_short_sequence_is_zero():
    E = np.zeros((4, 2))
    assert roughness(E) == 0.0
