"""
A small Laplace-smoothed trigram language model, trained on the same local
corpus as the embeddings. This is deliberately not a neural LM -- it exists
only to give guided_rewrite.py a cheap, honest fluency signal ("does this
substitution still read like English") without pulling in a multi-hundred-
megabyte pretrained model. See FEASIBILITY.md for the tradeoff this implies.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from functools import lru_cache

from .corpus import training_sentences

_BOS = "<s>"
_EOS = "</s>"


class TrigramLM:
    def __init__(self, sentences: list[list[str]]):
        self.vocab: set[str] = set()
        self.unigram: Counter = Counter()
        self.bigram: Counter = Counter()
        self.trigram: Counter = Counter()
        self.bigram_context: Counter = Counter()  # counts of (w1, w2) as context
        for sent in sentences:
            padded = [_BOS, _BOS] + sent + [_EOS]
            self.vocab.update(sent)
            for w in padded:
                self.unigram[w] += 1
            for i in range(len(padded) - 1):
                self.bigram[(padded[i], padded[i + 1])] += 1
            for i in range(len(padded) - 2):
                ctx = (padded[i], padded[i + 1])
                self.trigram[(ctx, padded[i + 2])] += 1
                self.bigram_context[ctx] += 1
        self.V = max(len(self.vocab), 1)

    def trigram_logprob(self, w1: str, w2: str, w3: str) -> float:
        ctx = (w1, w2)
        num = self.trigram[(ctx, w3)] + 1
        den = self.bigram_context[ctx] + self.V
        return math.log(num / den)

    def sentence_logprob(self, tokens: list[str]) -> float:
        padded = [_BOS, _BOS] + list(tokens) + [_EOS]
        total = 0.0
        for i in range(len(padded) - 2):
            total += self.trigram_logprob(padded[i], padded[i + 1], padded[i + 2])
        return total

    def sentence_logprob_per_token(self, tokens: list[str]) -> float:
        if not tokens:
            return 0.0
        return self.sentence_logprob(tokens) / len(tokens)


@lru_cache(maxsize=1)
def get_lm() -> TrigramLM:
    return TrigramLM(training_sentences())
