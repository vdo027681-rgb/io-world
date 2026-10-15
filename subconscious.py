import math
import numpy as np


class Subconscious:
    """Трансформер подсознания Ио: внимание, полный обратный проход."""

    def __init__(self, vocab, d=16, lr=0.2, seed=3):
        self.rng = np.random.default_rng(seed)
        self.vocab = list(vocab)
        self.vidx = {w: i for i, w in enumerate(self.vocab)}
        self.V, self.d, self.lr = len(self.vocab), d, lr
        r = self.rng.normal
        self.Em = r(0, 0.1, (self.V, d))
        self.Wq = r(0, 0.1, (d, d))
        self.Wk = r(0, 0.1, (d, d))
        self.Wv = r(0, 0.1, (self.V, d))   # таблица значений по токенам
        self.head = r(0, 0.1, (d, self.V))

    def encode(self, tokens):
        return np.stack([self.Em[self.vidx[t]] for t in tokens])

    def forward(self, tokens):
        X = self.encode(tokens)
        Q = X @ self.Wq
        K = X @ self.Wk
        Vt = self.Wv[[self.vidx[t] for t in tokens]]   # (T, d)
        S = np.exp(Q @ K.T / math.sqrt(self.d))
        S = S / S.sum(axis=1, keepdims=True)
        H = S @ Vt
        logits = H @ self.head
        return {"X": X, "Q": Q, "K": K, "V": Vt, "S": S,
                "H": H, "logits": logits}

    def train_step(self, window):
        if len(window) < 2:
            return None
        tokens = [w for w in window if w in self.vidx]
        if len(tokens) < 2:
            return None
        f = self.forward(tokens)
        logits = f["logits"]
        shifted = tokens[1:] + [tokens[0]]  # предсказание следующего
        y = np.array([self.vidx[t] for t in shifted])
        m = logits.max(axis=1, keepdims=True)
        e = np.exp(logits - m)
        probs = e / e.sum(axis=1, keepdims=True)
        loss = -np.log(probs[np.arange(len(y)), y] + 1e-9).mean()
        # обратный проход
        dlogits = probs.copy()
        dlogits[np.arange(len(y)), y] -= 1.0
        dlogits /= len(y)
        gH = dlogits @ self.head.T                    # (T, d)
        dhead = f["H"].T @ dlogits                    # (d, V)
        norm = np.linalg.norm(dhead) + 1e-9
        self.head -= self.lr * (dhead / norm * 3.0)   # нормирован и усилен втрое
        dS = gH @ f["V"].T                            # (T, T)
        dV = f["S"].T @ gH                            # (T, d)
        dQ = dS @ f["K"]
        dK = dS.T @ f["Q"]
        dEm = dQ @ self.Wq.T + dK @ self.Wk.T
        for i, t in enumerate(tokens):
            j = self.vidx[t]
            self.Em[j] -= self.lr * dEm[i]
            self.Wv[j] -= self.lr * dV[i]
        self.Wq -= self.lr * (f["X"].T @ dQ)
        self.Wk -= self.lr * (f["X"].T @ dK)
        return float(loss)

    def answer(self, prompt, max_len=8):
        words = prompt.split()
        if not words:
            return "..."
        known = [w for w in words if w in self.vidx]
        if not known:
            return "не знаю таких слов: " + " ".join(words)
        out = [known[-1]]
        last = self.vidx[known[-1]]
        for _ in range(max_len):
            logits = self.forward(out)["logits"][-1]
            idx = list(np.argsort(logits)[::-1][:5])
            pick = int(self.rng.choice(idx[:3])) if len(idx) > 0 else last
            if self.vocab[pick] in out:
                pick = int(self.rng.integers(0, self.V))
            out.append(self.vocab[pick])
            last = pick
        return " ".join(out)


def build_vocab(text, min_count=2, limit=160):
    counts = {}
    for w in text.split():
        counts[w] = counts.get(w, 0) + 1
    words = [w for w, c in counts.items() if c >= min_count]
    words.sort(key=lambda w: -counts[w])
    return words[:limit]
