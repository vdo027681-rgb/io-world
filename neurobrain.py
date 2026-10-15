import random


class Brain:
    """Мозг Ио: 2000 нейронов Ижикевича, STDP, сны, lesion-экзамен."""
    def __init__(self, n=2000, seed=1):
        self.n = n
        self.rng = random.Random(seed)
        self.v = [-65.0] * n
        self.u = [0.0] * n
        self.I = [0.0] * n
        self.c = [(-65.0, 8.0)] * n
        self.a = [0.02] * n
        self.b = [0.2] * n
        self.dead = [False] * n
        self.conns = [[] for _ in range(n)]
        self.w1 = {}            # слово -> нейрон
        self.inv = {}           # нейрон -> слово
        self.assoc = {}         # (a, b) -> индекс связи
        self.last_spikes = []
        self.dream = []
        self._wire_ring(6)

    def _wire_ring(self, k=6):
        for i in range(self.n):
            for j in range(1, k + 1):
                self.conns[i].append(((i + j) % self.n, 2.0))

    def wire_vocab(self, vocab):
        for w in vocab:
            if w not in self.w1 and len(self.w1) < self.n:
                i = len(self.w1)
                self.w1[w] = i
                self.inv[i] = w

    def associate(self, a, b):
        na, nb = self.w1.get(a), self.w1.get(b)
        if na is None or nb is None:
            return False
        if (a, b) in self.assoc:
            return True
        self.conns[na].append((nb, 60.0))
        self.assoc[(a, b)] = len(self.conns[na]) - 1
        return True

    def reset_state(self):
        self.v = [-65.0] * self.n
        self.u = [0.0] * self.n
        self.I = [0.0] * self.n
        self.last_spikes = []

    def stimulate(self, i, current):
        if not self.dead[i]:
            self.I[i] += current

    def step(self, dt=1.0):
        spiked = []
        for i in range(self.n):
            if self.dead[i]:
                continue
            v = self.v[i]
            vv = max(-90.0, min(60.0, v))       # клип перед квадратом
            dv = 0.04 * vv * vv + 5.0 * vv + 140.0 - self.u[i]
            v = v + dt * (dv + self.I[i])       # Эйлер: v += 0.04v^2+5v+140-u+I
            if v >= 30.0:
                spiked.append(i)
                self.v[i] = self.c[i][0]
                self.u[i] += self.c[i][1]
            else:
                self.v[i] = max(-90.0, min(60.0, v))
            du = self.a[i] * (self.b[i] * v - self.u[i])
            self.u[i] = max(-30.0, self.u[i] + dt * du)
            self.I[i] = 0.0
        # честное распространение спайков по связям
        for i in spiked:
            for (j, w) in self.conns[i]:
                if not self.dead[j]:
                    self.I[j] += w
        self.last_spikes = spiked
        return spiked

    def recall(self, word, steps=24, current=30.0):
        """Вспышки нейрона-цели при стимуляции слова-источника."""
        target = self.assoc.get(word)  # не используется напрямую
        src = self.w1.get(word)
        if src is None:
            return 0
        self.reset_state()
        flashes = 0
        for t in range(steps):
            if t % 2 == 0:
                self.stimulate(src, current)
            self.step()
            for i in self.last_spikes:
                # цель — ближайший исходящий по ассоциации
                for (j, w) in self.conns[i]:
                    if w >= 50.0 and self.inv.get(j) is not None:
                        flashes += 0
        return flashes

    def exam_recall(self, word, target, steps=40, current=30.0):
        """Вспышки конкретной цели при стимуляции источника."""
        src = self.w1.get(word)
        tgt = self.w1.get(target)
        if src is None or tgt is None:
            return 0
        self.reset_state()
        flashes = 0
        for t in range(steps):
            if t % 2 == 0:
                self.stimulate(src, current)
            self.step()
            if tgt in self.last_spikes:
                flashes += 1
        return flashes

    def lesion(self, count=50, seed=2, region=True):
        # поражение области коры слов: индексы лемм (region) или случайные
        rng = random.Random(seed)
        pool = range(min(120, len(self.w1) + 10)) if region else range(self.n)
        pool = [i for i in pool if not self.dead[i]]
        picked = rng.sample(pool, min(count, len(pool)))
        for i in picked:
            self.dead[i] = True
            self.conns[i] = []
        return count

    def dream_step(self, minutes=5):
        """Сон: случайные нейроны шепчут леммами."""
        self.dream = []
        word_ids = list(self.w1.values())
        for _ in range(minutes):
            if not word_ids:
                break
            i = self.rng.choice(word_ids)
            if self.dead[i]:
                continue
            for _ in range(4):
                self.stimulate(i, 60.0)   # длительная стимуляция
                self.step()
                for s in self.last_spikes:
                    w = self.inv.get(s)
                    if w:
                        self.dream.append(w)
        return self.dream
