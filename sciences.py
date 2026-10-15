import math

def correlation(xs, ys):
    n = len(xs)
    if n < 2:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx == 0.0 or sy == 0.0:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


class Hypothesis:
    def __init__(self, name, threshold=0.7):
        self.name = name
        self.threshold = threshold
        self.accepted = False
        self.r = 0.0

    def test(self, xs, ys):
        self.r = correlation(xs, ys)
        self.accepted = abs(self.r) >= self.threshold
        return self.accepted


class Science:
    def __init__(self):
        self.hypotheses = {}
        self.facts = []

    def propose(self, name, threshold=0.7):
        h = Hypothesis(name, threshold)
        self.hypotheses[name] = h
        return h

    def add_fact(self, text):
        if text not in self.facts:
            self.facts.append(text)
