"""
A small word-level neural (LSTM) language model, trained from scratch on
the same local corpus as everything else in this package.

Why this exists: the follow-up experiment in FEASIBILITY.md ("is WordNet
specifically the bottleneck?") found that relaxing candidate substitutions
beyond WordNet synonyms does close real distance to the spectral target,
but produces incoherent text, because ngram_lm.TrigramLM can only
recognize fluency it has memorized verbatim -- an unseen-but-grammatical
trigram ("man walked slowly") and an unseen nonsensical one ("man told
abandon") score almost identically under Laplace smoothing. A neural LM's
learned embeddings let it generalize past exact n-gram memorization, which
is what a real fluency judge (and real candidate proposer) needs.

A pretrained model (GPT-2 etc.) would generalize better with less data,
but huggingface.co and download.pytorch.org are both blocked by this
environment's network policy (confirmed via direct curl -- 403), so this
trains a small model from scratch on the ~30k-sentence local corpus
instead. That's a real tradeoff, not a free upgrade -- see FEASIBILITY.md
for what it does and doesn't fix.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from .corpus import training_sentences

PAD, BOS, EOS, UNK = "<pad>", "<s>", "</s>", "<unk>"
SPECIAL_TOKENS = (PAD, BOS, EOS, UNK)

_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", ".cache")
_MODEL_PATH = os.path.join(_CACHE_DIR, "neural_lm.pt")


@dataclass
class Vocab:
    word_to_id: dict
    id_to_word: list

    @classmethod
    def build(cls, sentences: list[list[str]], min_count: int = 3) -> "Vocab":
        from collections import Counter

        counts = Counter(w for s in sentences for w in s)
        words = [w for w, c in counts.items() if c >= min_count]
        words.sort()
        id_to_word = list(SPECIAL_TOKENS) + words
        word_to_id = {w: i for i, w in enumerate(id_to_word)}
        return cls(word_to_id=word_to_id, id_to_word=id_to_word)

    def __len__(self) -> int:
        return len(self.id_to_word)

    def encode(self, word: str) -> int:
        return self.word_to_id.get(word, self.word_to_id[UNK])

    def encode_seq(self, tokens: list[str]) -> list[int]:
        return [self.encode(w) for w in tokens]


def _build_model(vocab_size: int, emb_dim: int = 128, hidden_dim: int = 256, num_layers: int = 1):
    import torch.nn as nn

    class LSTMLM(nn.Module):
        def __init__(self):
            super().__init__()
            self.embed = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
            self.lstm = nn.LSTM(emb_dim, hidden_dim, num_layers=num_layers, batch_first=True)
            self.out = nn.Linear(hidden_dim, vocab_size)

        def forward(self, x, hidden=None):
            e = self.embed(x)
            h, hidden = self.lstm(e, hidden)
            return self.out(h), hidden

    return LSTMLM()


def _make_training_stream(vocab: Vocab, sentences: list[list[str]]) -> list[int]:
    stream = []
    for s in sentences:
        stream.append(vocab.encode(BOS))
        stream.extend(vocab.encode_seq(s))
        stream.append(vocab.encode(EOS))
    return stream


def train_neural_lm(
    seq_len: int = 32,
    batch_size: int = 64,
    epochs: int = 5,
    emb_dim: int = 128,
    hidden_dim: int = 256,
    lr: float = 2e-3,
    verbose: bool = True,
    sentences: list[list[str]] | None = None,
    save: bool = True,
    save_path: str | None = None,
):
    import torch
    import torch.nn as nn

    sentences = sentences if sentences is not None else training_sentences()
    vocab = Vocab.build(sentences, min_count=1 if len(sentences) < 1000 else 3)
    stream = _make_training_stream(vocab, sentences)

    n_chunks = len(stream) // seq_len
    data = torch.tensor(stream[: n_chunks * seq_len], dtype=torch.long).view(n_chunks, seq_len)
    n_val = max(1, int(0.05 * n_chunks))
    train_data, val_data = data[:-n_val], data[-n_val:]

    model = _build_model(len(vocab), emb_dim, hidden_dim)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss(ignore_index=vocab.word_to_id[PAD])

    def run_epoch(data_tensor, train: bool):
        model.train(train)
        perm = torch.randperm(data_tensor.size(0)) if train else torch.arange(data_tensor.size(0))
        total_loss, total_tokens = 0.0, 0
        for i in range(0, len(perm), batch_size):
            idx = perm[i : i + batch_size]
            batch = data_tensor[idx]
            inputs, targets = batch[:, :-1], batch[:, 1:]
            logits, _ = model(inputs)
            loss = loss_fn(logits.reshape(-1, logits.size(-1)), targets.reshape(-1))
            if train:
                opt.zero_grad()
                loss.backward()
                opt.step()
            total_loss += loss.item() * targets.numel()
            total_tokens += targets.numel()
        return total_loss / max(total_tokens, 1)

    for epoch in range(epochs):
        train_loss = run_epoch(train_data, train=True)
        val_loss = run_epoch(val_data, train=False)
        if verbose:
            import math

            print(f"epoch {epoch+1}/{epochs} train_loss={train_loss:.3f} "
                  f"val_loss={val_loss:.3f} val_ppl={math.exp(val_loss):.1f}")

    if not save:
        return model, vocab

    path = save_path or _MODEL_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save(
        dict(
            state_dict=model.state_dict(),
            word_to_id=vocab.word_to_id,
            id_to_word=vocab.id_to_word,
            emb_dim=emb_dim,
            hidden_dim=hidden_dim,
        ),
        path,
    )
    return model, vocab


class NeuralLM:
    """Same fluency-scoring interface as ngram_lm.TrigramLM
    (sentence_logprob / sentence_logprob_per_token), so it can be passed
    anywhere a TrigramLM is currently accepted (e.g. guided_rewrite's `lm`
    argument) as a drop-in fluency judge. Adds topk_next_words for
    candidate proposal (see rewrite.neural_candidates).
    """

    def __init__(self, model, vocab: Vocab):
        self.model = model
        self.vocab = vocab
        self.model.eval()

    def _logits_for_context(self, context_ids: list[int]):
        import torch

        with torch.no_grad():
            x = torch.tensor([context_ids], dtype=torch.long)
            logits, _ = self.model(x)
            return logits[0]  # (len(context_ids), vocab_size)

    def sentence_logprob(self, tokens: list[str]) -> float:
        import torch
        import torch.nn.functional as F

        ids = [self.vocab.encode(BOS)] + self.vocab.encode_seq(tokens) + [self.vocab.encode(EOS)]
        logits = self._logits_for_context(ids[:-1])
        targets = torch.tensor(ids[1:], dtype=torch.long)
        log_probs = F.log_softmax(logits, dim=-1)
        token_lp = log_probs.gather(1, targets.unsqueeze(1)).squeeze(1)
        return float(token_lp.sum().item())

    def sentence_logprob_per_token(self, tokens: list[str]) -> float:
        if not tokens:
            return 0.0
        return self.sentence_logprob(tokens) / len(tokens)

    def topk_next_words(self, context_tokens: list[str], top_k: int = 12) -> list[str]:
        import torch
        import torch.nn.functional as F

        ids = [self.vocab.encode(BOS)] + self.vocab.encode_seq(context_tokens)
        logits = self._logits_for_context(ids)[-1]
        probs = F.log_softmax(logits, dim=-1)
        top_ids = torch.topk(probs, k=min(top_k * 2, len(self.vocab))).indices.tolist()
        words = [self.vocab.id_to_word[i] for i in top_ids if self.vocab.id_to_word[i] not in SPECIAL_TOKENS]
        return words[:top_k]


def load_neural_lm(path: str) -> NeuralLM:
    """Load a NeuralLM from an arbitrary checkpoint path (not cached) --
    used to keep multiple trained variants around side by side, e.g. to
    compare the 30k-sentence model against a full-corpus retrain without
    overwriting the first one.
    """
    import torch

    ckpt = torch.load(path, weights_only=True)
    vocab = Vocab(word_to_id=ckpt["word_to_id"], id_to_word=ckpt["id_to_word"])
    model = _build_model(len(vocab), ckpt["emb_dim"], ckpt["hidden_dim"])
    model.load_state_dict(ckpt["state_dict"])
    return NeuralLM(model, vocab)


@lru_cache(maxsize=1)
def get_neural_lm() -> NeuralLM:
    if not os.path.exists(_MODEL_PATH):
        model, vocab = train_neural_lm()
        return NeuralLM(model, vocab)
    return load_neural_lm(_MODEL_PATH)
