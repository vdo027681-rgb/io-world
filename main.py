"""
Мир Ио — монолитная версия: физика, планета, мозг, подсознание, наука, мир и
интерфейс в одном файле.
Консоль: python main.py --console
Графика: python main.py
Команды: прожить N, тик, мир, статус, вопрос ..., обучить N, скачать N,
         сон, диагностика, гипотеза, бросить, сохранить, дневник, выход
"""
import os, sys, json, math, random

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE = os.path.join(HERE, "save.json")
SEED = os.path.join(HERE, "library", "seed.txt")

try:
    import numpy as np
except Exception:
    np = None


# ---------------------------------------------------------------- ошибки
def crash_log(text):
    for p in [os.path.join(HERE, "io_crash.log"),
              "/storage/emulated/0/Download/io_crash.log"]:
        try:
            with open(p, "a", encoding="utf-8") as f:
                f.write(text)
            return p
        except Exception:
            pass
    return None


def show_error(err):
    path = crash_log(err)
    text = err
    if path:
        text += "\n\n(записано в %s)" % path
    try:
        from kivy.app import App as KApp
        from kivy.uix.label import Label
        from kivy.uix.scrollview import ScrollView

        class ErrApp(KApp):
            def build(self):
                lab = Label(text=text[:6000], font_size="11sp",
                            halign="left", valign="top")
                lab.bind(size=lab.setter("text_size"))
                lab.bind(texture_size=lab.setter("size"))
                sv = ScrollView()
                sv.add_widget(lab)
                return sv

        ErrApp().run()
        return
    except Exception:
        pass
    sys.stderr.write(err)


# ---------------------------------------------------------------- наука
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


# ---------------------------------------------------------------- физика
class Throw:
    """Бросок тела: g = 9.81, шаг 0.01 с, без сопротивления воздуха."""

    def __init__(self, v0=20.0, angle=45.0, g=9.81):
        self.v0, self.angle, self.g = v0, math.radians(angle), g

    def run(self):
        self.pts = [(0.0, 0.0)]
        x = y = 0.0
        vx = self.v0 * math.cos(self.angle)
        vy = self.v0 * math.sin(self.angle)
        while y >= 0.0 and len(self.pts) < 100000:
            x += vx * 0.01
            vy -= self.g * 0.01
            y += vy * 0.01
            self.pts.append((x, y))

    def audit(self):
        """Проверка закона: x(t) = v0*cos*t, y(t) = v0*sin*t - g*t^2/2."""
        ok = True
        vx = self.v0 * math.cos(self.angle)
        vy = self.v0 * math.sin(self.angle)
        for i, (x, y) in enumerate(self.pts):
            t = i * 0.01
            ex = vx * t
            ey = vy * t - 0.5 * self.g * t * t
            if abs(x - ex) > 1e-6 or abs(y - ey) > 1e-6:
                ok = False
                break
        return ok, []

    def results(self):
        rng = self.pts[-1][0] if self.pts else 0.0
        apex = max(y for _, y in self.pts) if self.pts else 0.0
        return rng, apex


# ---------------------------------------------------------------- математика
def is_prime(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def safe_calc(expr):
    allowed = set("0123456789+-*/(). ")
    if not expr or not set(expr) <= allowed:
        return "только числа и + - * / ( )"
    try:
        return str(eval(expr, {"__builtins__": {}}, {}))
    except Exception:
        return "не понял выражение"


# ---------------------------------------------------------------- планета
GRID = 51
PLACES = {"дом": (10, 10), "корпорация Ио": (25, 25),
          "магазин": (40, 15), "библиотека": (15, 38), "парк": (38, 40)}
LETTERS = {"дом": "Д", "корпорация Ио": "К", "магазин": "М",
           "библиотека": "Б", "парк": "П"}
PLACE_COLORS = {"дом": (0.85, 0.65, 0.25), "корпорация Ио": (0.85, 0.3, 0.3),
                "магазин": (0.3, 0.55, 0.9), "библиотека": (0.6, 0.35, 0.85),
                "парк": (0.3, 0.75, 0.4)}


class Body:
    def __init__(self):
        self.x, self.y = PLACES["дом"]
        self.coins = 20
        self.energy = 80.0


class Planet:
    def __init__(self):
        self.day = 1
        self.tick = 0
        self.cloud = 0.3
        self.body = Body()
        rng = random.Random(1)
        self.food = {}
        for _ in range(30):
            gx, gy = rng.randrange(2, GRID - 2), rng.randrange(2, GRID - 2)
            self.food[(gx, gy)] = rng.choice([2, 3, 5])

    def sunlight(self):
        # 48 тиков в сутках: свет с 6-го по 42-й тик, синус
        if 6 <= self.tick <= 42:
            return max(0.0, math.sin(math.pi * (self.tick - 6) / 36.0)) * (1 - self.cloud)
        return 0.0

    def temperature(self):
        return 10.0 + 12.0 * self.sunlight()

    def step(self):
        self.tick += 1
        if self.tick >= 48:
            self.tick = 0
            self.day += 1
            self.cloud = max(0.0, min(1.0, self.cloud + random.uniform(-0.2, 0.2)))
        sun = self.sunlight()
        if sun > 0.4:
            for k in list(self.food):
                self.food[k] = min(8.0, self.food[k] + 0.05 * sun)
        else:
            for k in list(self.food):
                self.food[k] = max(0.5, self.food[k] - 0.02)
        self.body.energy = max(0.0, self.body.energy - 0.5)

    def clock(self):
        return "%02d:%02d" % (self.tick // 2, (self.tick % 2) * 30)


# ---------------------------------------------------------------- общество
class Society:
    def __init__(self, pl):
        self.pl = pl
        self.mood = "спокойно"
        self.task_done_today = False
        self.diary_all = []
        self.food_log = []
        self._plan = []

    def plan_day(self):
        body = self.pl.body
        plan = ["дом"] * 48
        for t in range(12, 40):          # рабочий день: 6:00–20:00
            plan[t] = "корпорация Ио"
        if body.coins < 15 or body.energy < 40:
            for t in range(40, 44):
                plan[t] = "магазин"
        return plan

    def step(self):
        if not self._plan:
            self._plan = self.plan_day()
        t = self.pl.tick
        place = self._plan[t] if t < len(self._plan) else "дом"
        px, py = PLACES.get(place, PLACES["дом"])
        self.pl.body.x, self.pl.body.y = float(px), float(py)
        if place == "корпорация Ио" and t in (20, 30):
            self.pl.body.coins += 10
            self.task_done_today = True
        if place == "магазин" and self.pl.body.coins >= 5:
            self.pl.body.coins -= 5
            self.pl.body.energy = min(100.0, self.pl.body.energy + 20.0)
        if self.pl.body.energy < 20:
            self.mood = "устал"
        elif self.task_done_today:
            self.mood = "доволен"

    def midnight(self):
        sun = self.pl.sunlight()
        total = sum(self.pl.food.values())
        self.food_log.append((sun, total))
        if len(self.food_log) > 60:
            self.food_log.pop(0)
        self.diary_all.append((self.pl.day,
                               "день %d: монет %d, еды %.0f, настроение: %s" % (
                                   self.pl.day, self.pl.body.coins, total, self.mood)))
        self.task_done_today = False

    def map_view(self):
        # грубая карта 17x17
        cell = GRID // 17
        grid = [["."] * 17 for _ in range(17)]
        for name, (px, py) in PLACES.items():
            grid[min(16, py // cell)][min(16, px // cell)] = LETTERS[name]
        bx = min(16, int(self.pl.body.x) // cell)
        by = min(16, int(self.pl.body.y) // cell)
        grid[by][bx] = "И"
        return "\n".join("".join(r) for r in grid)


# ---------------------------------------------------------------- мозг (Ижикевич)
class Brain:
    def __init__(self, n=2000):
        rng = random.Random(42)
        self.n = n
        self.a, self.b, self.c, self.d = [], [], [], []
        self.v, self.u, self.dead = [], [], [False] * n
        self.fired = [False] * n
        for _ in range(n):
            regular = rng.random() < 0.8
            self.a.append(0.02 if regular else 0.1)
            self.b.append(0.2 if regular else 0.25)
            self.c.append(-65.0 if regular else -55.0)
            self.d.append(8.0 if regular else 4.0)
        for i in range(n):
            self.v.append(-65.0)
            self.u.append(-65.0 * self.b[i])
        self.next_I = [0.0] * n
        self.vocab = {}
        self.assoc = set()

    def _wire_ring(self, k=6):
        self.ring = k

    def wire_vocab(self, lemmas):
        self.vocab = {w: (i * 7 + 3) % self.n for i, w in enumerate(lemmas)}
        self._wire_ring(6)

    def _inject(self, i, val):
        if 0 <= i < self.n and not self.dead[i]:
            self.next_I[i] += val

    def _propagate(self):
        ring = self.ring
        for i in range(self.n):
            if self.fired[i] and not self.dead[i]:
                for k in range(1, ring // 2 + 1):
                    self._inject((i + k) % self.n, 2.0)
                    self._inject((i - k) % self.n, 2.0)

    def step(self, steps=1, source=None):
        for _ in range(steps):
            self._propagate()
            I = self.next_I
            self.next_I = [0.0] * self.n
            for i in range(self.n):
                if self.dead[i]:
                    self.fired[i] = False
                    continue
                v, u = self.v[i], self.u[i]
                v += 0.04 * v * v + 5.0 * v + 140.0 - u + I[i]
                if v >= 30.0:
                    v = 30.0
                u += self.a[i] * (self.b[i] * v - u)
                if v >= 30.0:
                    self.fired[i] = True
                    v = self.c[i]
                    u += self.d[i]
                else:
                    self.fired[i] = False
                self.v[i], self.u[i] = v, u

    def associate(self, a, b):
        if a in self.vocab and b in self.vocab and (a, b) not in self.assoc:
            self.assoc.add((a, b))
            return True
        return False

    def exam_recall(self, a, b):
        ia, ib = self.vocab.get(a), self.vocab.get(b)
        if ia is None or ib is None or self.dead[ia] or self.dead[ib]:
            return 0
        for t in range(24):
            self._inject(ia, 60.0)
            if (a, b) in self.assoc:
                self._inject(ib, 60.0)
            self.step(1)
            if self.fired[ib]:
                return 1
        return 0

    def dream_step(self):
        if not self.assoc:
            return []
        pair = random.choice(list(self.assoc))
        self.exam_recall(*pair)
        return [pair[0], pair[1]]

    def lesion(self, k=50, seed=0):
        rng = random.Random(seed)
        killed = 0
        while killed < k and killed < self.n:
            i = rng.randrange(self.n)
            if not self.dead[i]:
                self.dead[i] = True
                killed += 1
        return killed


# ---------------------------------------------------------------- подсознание
def build_vocab(text, min_count=1, limit=160):
    counts = {}
    for w in text.split():
        counts[w] = counts.get(w, 0) + 1
    words = [w for w, c in counts.items() if c >= min_count]
    words.sort(key=lambda w: -counts[w])
    return words[:limit]


class Subconscious:
    """Мини-трансформер: эмбеддинги + одно внимание + линейный выход."""

    def __init__(self, lemmas, lr=0.2):
        self.lemmas = list(lemmas)
        self.vidx = {w: i for i, w in enumerate(self.lemmas)}
        self.lr = lr
        E, D = max(1, len(self.lemmas)), 16
        if np is None:
            self.ok = False
            return
        self.ok = True
        rng = np.random.RandomState(7)
        self.emb = rng.randn(E, D) * 0.1
        self.Wq = rng.randn(D, D) / math.sqrt(D)
        self.Wk = rng.randn(D, D) / math.sqrt(D)
        self.Wv = rng.randn(D, D) / math.sqrt(D)
        self.Wo = rng.randn(D, E) / math.sqrt(D)

    def _attend(self, toks):
        idx = [self.vidx[t] for t in toks if t in self.vidx]
        if not idx:
            return None, None
        X = self.emb[idx]                       # (L, D)
        Q, K, V = X @ self.Wq, X @ self.Wk, X @ self.Wv
        S = Q @ K.T / math.sqrt(X.shape[1])
        S = S - S.max(axis=1, keepdims=True)
        A = np.exp(S)
        A /= A.sum(axis=1, keepdims=True)
        H = A @ V                               # (L, D)
        return H, idx

    def train_step(self, toks):
        if not self.ok:
            return 0.0
        H, idx = self._attend(toks[:-1])
        if H is None or len(idx) < 2:
            return 0.0
        logits = H @ self.Wo                    # (L, E)
        target = idx[1:]                        # следующий токен
        logits -= logits.max(axis=1, keepdims=True)
        P = np.exp(logits)
        P /= P.sum(axis=1, keepdims=True)
        L = len(target)
        loss = -math.log(max(P[np.arange(L), target].min(), 1e-9))
        # обратный проход (упрощённо, по всем позициям)
        dlog = P
        dlog[np.arange(L), target] -= 1.0
        dWo = H.T @ dlog
        dH = dlog @ self.Wo.T
        dX = dH @ self.Wv.T
        for j, i in enumerate(idx):
            self.emb[i] -= self.lr * dX[j]
        self.Wo -= self.lr * dWo / max(1, L)
        return loss

    def answer(self, q, steps=8):
        if not self.ok or not self.lemmas:
            return "..."
        toks = [w for w in q.split() if w in self.vidx]
        if not toks:
            return random.choice(self.lemmas)
        out = list(toks)
        for _ in range(steps):
            H, _ = self._attend(out[-8:])
            if H is None:
                break
            logits = H[-1] @ self.Wo
            out.append(self.lemmas[int(np.argmax(logits))])
        return " ".join(out)


# ---------------------------------------------------------------- библиотека
def fetch_download(word, max_chars=300000):
    try:
        import requests
    except Exception:
        return None
    urls = {"вертер": ["https://www.gutenberg.org/cache/epub/24099/pg24099.txt"]}
    for u in urls.get(word, []):
        try:
            r = requests.get(u, timeout=15)
            if r.status_code == 200:
                text = r.text[:max_chars]
                lib = os.path.join(HERE, "library")
                try:
                    os.makedirs(lib, exist_ok=True)
                except OSError:
                    return None
                path = os.path.join(lib, word + ".txt")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
                return path
        except Exception:
            pass
    return None


# ---------------------------------------------------------------- приложение
class App:
    def __init__(self):
        self.pl = Planet()
        self.soc = Society(self.pl)
        self.sci = Science()
        self.brain = Brain()
        self.sub = None
        self.counts = {}
        self.lemmas = []
        self.text = ""
        self._load_corpus()

    def _load_corpus(self):
        text = ""
        if os.path.exists(SEED):
            try:
                with open(SEED, "r", encoding="utf-8") as f:
                    text = f.read()
            except OSError:
                pass
        lib = os.path.join(HERE, "library")
        if os.path.isdir(lib):
            for fn in os.listdir(lib):
                if fn.endswith(".txt") and fn != "seed.txt":
                    try:
                        with open(os.path.join(lib, fn), "r", encoding="utf-8") as f:
                            text += " " + f.read()
                    except OSError:
                        pass
        self.text = text
        self.lemmas = build_vocab(text, min_count=1, limit=160)
        self.brain.wire_vocab(self.lemmas)
        self.sub = Subconscious(self.lemmas, lr=0.2)
        self.counts = {}
        if self.sub.ok:
            toks = [w for w in text.split() if w in self.sub.vidx]
            for a, b in zip(toks, toks[1:]):
                self.counts[(a, b)] = self.counts.get((a, b), 0) + 1

    def intelligence(self):
        logic = 40 + 10 * len(self.sci.hypotheses) + 5 * sum(
            1 for h in self.sci.hypotheses.values() if h.accepted)
        memory = 30 + min(50, len(self.lemmas) // 3)
        knowledge = 20 + min(60, len(self.sci.facts) * 10 + len(self.text) // 4000)
        wisdom = min(80, 10 * len(self.brain.assoc) + len(self.sci.facts) * 8)
        wit = 35 + min(45, len(self.counts) // 50)
        return {"логика": min(100, logic), "память": min(100, memory),
                "знание": min(100, knowledge), "мудрость": max(0, min(100, wisdom)),
                "сообразительность": min(100, wit)}

    def save(self):
        data = {
            "day": self.pl.day, "tick": self.pl.tick,
            "coins": self.pl.body.coins, "energy": self.pl.body.energy,
            "x": self.pl.body.x, "y": self.pl.body.y,
            "lemmas": self.lemmas,
            "facts": self.sci.facts,
            "hypotheses": {k: (v.accepted, v.r) for k, v in self.sci.hypotheses.items()},
            "counts": {"\x1f".join(k) if isinstance(k, tuple) else k: v
                       for k, v in self.counts.items()},
            "diary": self.soc.diary_all,
            "assoc": [list(k) for k in self.brain.assoc],
        }
        try:
            with open(SAVE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            return True
        except OSError:
            return False

    def load(self):
        if not os.path.exists(SAVE):
            return False
        try:
            with open(SAVE, "r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            return False
        try:
            self.pl.day = d["day"]
            self.pl.tick = d.get("tick", 0)
            self.pl.body.coins = d["coins"]
            self.pl.body.energy = d["energy"]
            self.pl.body.x, self.pl.body.y = d["x"], d["y"]
            self.lemmas = d["lemmas"]
            self.brain.wire_vocab(self.lemmas)
            self.sub = Subconscious(self.lemmas, lr=0.2)
            self.sci.facts = d["facts"]
            self.counts = {}
            for k, v in d["counts"].items():
                key = tuple(k.split("\x1f")) if "\x1f" in k else k
                self.counts[key] = v
            for name, (acc, r) in d.get("hypotheses", {}).items():
                h = self.sci.propose(name)
                h.accepted, h.r = acc, r
            for (a, b) in d.get("assoc", []):
                self.brain.associate(a, b)
            self.soc.diary_all = [tuple(x) for x in d.get("diary", [])]
            return True
        except Exception:
            return False

    def _step_once(self):
        if not self.soc._plan:
            self.soc._plan = self.soc.plan_day()
        self.pl.step()
        self.soc.step()
        if self.pl.tick == 0:
            self.soc.midnight()
            self.soc._plan = None

    def cmd_tick(self):
        self._step_once()
        plan = self.soc._plan
        act = plan[self.pl.tick - 1] if plan and self.pl.tick > 0 else "дом"
        act = {"дом": "дома", "корпорация Ио": "на работе",
               "магазин": "в магазине"}.get(act, act)
        return "день %d, %s — Ио %s, монеты %d, энергия %.0f" % (
            self.pl.day, self.pl.clock(), act, self.pl.body.coins, self.pl.body.energy)

    def cmd_live(self, n=1):
        for _ in range(n):
            for _ in range(48):
                self._step_once()
            self.soc.midnight()
            self.soc._plan = None

    def cmd_world(self):
        return self.soc.map_view()

    def cmd_status(self):
        b = self.pl.body
        intel = self.intelligence()
        return ("день %d, %s, облачность %.2f, температура %.1f C\n"
                "монеты %d, энергия %.0f, настроение: %s\n"
                "лемм %d, биграмм %d, фактов %d, дела: %s\n"
                "интеллект: %s" % (
                    self.pl.day, self.pl.clock(), self.pl.cloud,
                    self.pl.temperature(), b.coins, b.energy, self.soc.mood,
                    len(self.lemmas), len(self.counts), len(self.sci.facts),
                    "выполнено" if self.soc.task_done_today else "ожидается",
                    ", ".join("%s %d" % (k, v) for k, v in intel.items())))

    def cmd_ask(self, q):
        ans = self.sub.answer(q)
        for w in q.split():
            tgt = [b for (a, b) in self.brain.assoc if a == w]
            if tgt:
                ans += " | " + " ".join(tgt)
        return ans

    def cmd_train(self, n=100):
        toks = [w for w in self.text.split() if w in self.sub.vidx]
        if len(toks) < 3:
            return "корпус пуст"
        rng = random.Random(9)
        loss0 = loss = None
        for i in range(n):
            t = rng.randrange(len(toks) - 8)
            loss = self.sub.train_step(toks[t:t + 8])
            if loss0 is None:
                loss0 = loss
        assoc = 0
        ranked = sorted(self.counts.items(), key=lambda kv: -kv[1])
        for (a, b), c in ranked:
            if assoc < 40:
                if self.brain.associate(a, b):
                    assoc += 1
        return "ошибка %.3f -> %.3f, ассоциаций +%d" % (loss0, loss, assoc)

    def cmd_download(self, chars=300):
        path = fetch_download("вертер", max_chars=max(1, int(chars)) * 1000)
        if path is None:
            return "источник не найден"
        self._load_corpus()
        return "скачано: %s, лемм теперь %d" % (os.path.basename(path), len(self.lemmas))

    def cmd_sleep(self):
        return "сон шепчет: " + " ".join(self.brain.dream_step()[:8])

    def cmd_diagnostics(self):
        ranked = sorted(self.counts.items(), key=lambda kv: -kv[1])
        pairs = [p for p, c in ranked if c >= 1][:5]
        if not pairs:
            L = self.lemmas
            pairs = [(L[i], L[i + 1]) for i in range(min(5, len(L) - 1))]
        if not pairs:
            return "мало данных для экзамена"
        for a, b in pairs:
            self.brain.associate(a, b)
        before = [self.brain.exam_recall(a, b) for a, b in pairs]
        self.brain.lesion(50, seed=self.pl.day)
        after = [self.brain.exam_recall(a, b) for a, b in pairs]
        phys = Throw(v0=20.0, angle=45.0)
        phys.run()
        ok, _ = phys.audit()
        rng, apex = phys.results()
        return ("экзамен до поражения: %s; после: %s\n"
                "бросок: дальность %.2f м, апекс %.2f м, закон %s" % (
                    before, after, rng, apex,
                    "соблюдён" if ok else "нарушен"))

    def cmd_hypothesis(self):
        h = self.sci.propose("еда растёт от солнца", 0.7)
        if len(self.soc.food_log) < 3:
            return "мало данных: %d дней" % len(self.soc.food_log)
        xs = [s for s, g in self.soc.food_log]
        ys = [g for s, g in self.soc.food_log]
        ok = h.test(xs, ys)
        self.sci.add_fact("еда растёт от солнца" if ok else "связь света и еды не найдена")
        return "гипотеза %s, корреляция %.2f" % ("принята" if ok else "отвергнута", h.r)

    def cmd_throw(self):
        t = Throw(v0=20.0, angle=45.0)
        t.run()
        ok, _ = t.audit()
        rng, apex = t.results()
        return "бросок: дальность %.2f м, апекс %.2f м, закон %s" % (
            rng, apex, "соблюдён" if ok else "нарушен")

    def cmd_diary(self, n=10):
        if not self.soc.diary_all:
            return "дневник пуст"
        return "\n".join(str(e[1]) for e in self.soc.diary_all[-n:])


# ---------------------------------------------------------------- карта (Kivy)
def run_kivy(core):
    from kivy.app import App as KApp
    from kivy.core.window import Window
    from kivy.clock import Clock
    from kivy.graphics import Color, Rectangle, Ellipse, Line
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.label import Label
    from kivy.uix.button import Button
    from kivy.uix.textinput import TextInput
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.widget import Widget

    class MapWidget(Widget):
        def __init__(self, core_, **kw):
            super(MapWidget, self).__init__(**kw)
            self.core = core_
            self._labs = {}
            for name, letter in LETTERS.items():
                lab = Label(text=letter, font_size="11sp", size_hint=(None, None))
                self._labs[name] = lab
                self.add_widget(lab)
            self.bind(size=lambda *a: self.redraw(),
                      pos=lambda *a: self.redraw())
            Clock.schedule_interval(self._tick, 1.0)

        def _tick(self, dt):
            self.redraw()

        def redraw(self):
            w, h = self.size
            if w < 10 or h < 10:
                return
            c = min(w, h) / float(GRID) / 2.0
            ox = self.x + (w - c * GRID) / 2.0
            oy = self.y + (h - c * GRID) / 2.0
            pl = self.core.pl
            sun = pl.sunlight()
            self.canvas.clear()
            with self.canvas:
                Color(0.04 + 0.30 * sun, 0.05 + 0.30 * sun, 0.10 + 0.25 * sun)
                Rectangle(pos=self.pos, size=self.size)
                maxf = max(pl.food.values()) if pl.food else 0.0
                for (gx, gy), val in pl.food.items():
                    if val <= 0:
                        continue
                    a = min(1.0, val / maxf) if maxf > 0 else 0.0
                    Color(0.10 + 0.25 * a, 0.15 + 0.55 * a, 0.12)
                    Rectangle(pos=(ox + gx * c, oy + gy * c), size=(c, c))
                Color(0.25, 0.55, 0.25, 0.9)
                Line(rectangle=(ox + 5 * c, oy + 5 * c, 10 * c, 10 * c), width=1.5)
                for name, (px, py) in PLACES.items():
                    Color(PLACE_COLORS[name])
                    Rectangle(pos=(ox + (px - 1.5) * c, oy + (py - 1.5) * c),
                              size=(3 * c, 3 * c))
                Color(1.0, 0.9, 0.2)
                r = max(5.0, 1.6 * c)
                Ellipse(pos=(ox + pl.body.x * c - r / 2.0,
                             oy + pl.body.y * c - r / 2.0), size=(r, r))
            for name, lab in self._labs.items():
                px, py = PLACES[name]
                lab.pos = (ox + px * c - lab.width / 2.0,
                           oy + py * c - lab.height / 2.0)

    class IoApp(KApp):
        title = "Ио"

        def build(self):
            try:
                Window.softinput_mode = "below_target"
            except Exception:
                pass
            self.log_lines = []
            root = BoxLayout(orientation="vertical", padding=6, spacing=6)

            self.status = Label(text=core.cmd_status(), size_hint=(1, None),
                                height=90, halign="left", valign="top",
                                font_size="13sp")
            self.status.bind(size=self.status.setter("text_size"))
            root.add_widget(self.status)

            self.map = MapWidget(core, size_hint=(1, 0.35))
            root.add_widget(self.map)

            self.out = Label(text="Ио ждёт команды", size_hint_y=None,
                             halign="left", valign="top", font_size="12sp")
            self.out.bind(texture_size=self.out.setter("height"))
            self.out.bind(size=self.out.setter("text_size"))
            sv = ScrollView()
            sv.add_widget(self.out)
            root.add_widget(sv)

            row = BoxLayout(size_hint=(1, None), height=44, spacing=6)
            self.inp = TextInput(hint_text="вопрос Ио...", multiline=False,
                                 font_size="14sp")
            self.inp.bind(on_text_validate=self.on_ask)
            row.add_widget(self.inp)
            ask_btn = Button(text="спросить", size_hint=(None, 1), width=110)
            ask_btn.bind(on_press=self.on_ask)
            row.add_widget(ask_btn)
            root.add_widget(row)

            grid = GridLayout(cols=3, size_hint=(1, None), height=44 * 4 + 16,
                              spacing=6, padding=0)
            for text, cb in (
                ("тик", self.do_tick),
                ("прожить день", self.do_live),
                ("мир", self.do_world),
                ("сон", self.do_sleep),
                ("гипотеза", self.do_hyp),
                ("диагностика", self.do_diag),
                ("бросить камень", self.do_throw),
                ("обучить", self.do_train),
                ("скачать текст", self.do_download),
                ("сохранить", self.do_save),
            ):
                b = Button(text=text)
                b.bind(on_press=cb)
                grid.add_widget(b)
            root.add_widget(grid)
            self.refresh_status()
            return root

        def log(self, text):
            self.log_lines.append(text)
            self.log_lines = self.log_lines[-60:]
            self.out.text = "\n\n".join(self.log_lines)

        def refresh_status(self):
            self.status.text = core.cmd_status()

        def diary_tail(self):
            d = core.cmd_diary(3)
            if d and d != "дневник пуст":
                return "\n--- дневник ---\n" + d
            return ""

        def on_ask(self, *a):
            q = self.inp.text.strip()
            if not q:
                return
            self.inp.text = ""
            self.log("вы: " + q + "\nИо: " + core.cmd_ask(q))

        def do_tick(self, *a):
            self.log(core.cmd_tick())
            self.refresh_status()

        def do_live(self, *a):
            core.cmd_live(1)
            self.refresh_status()
            self.log("Ио прожил день" + self.diary_tail())

        def do_world(self, *a):
            self.log("карта мира:\n" + core.cmd_world())

        def do_sleep(self, *a):
            self.log(core.cmd_sleep())

        def do_hyp(self, *a):
            self.log(core.cmd_hypothesis())
            self.refresh_status()

        def do_diag(self, *a):
            self.log(core.cmd_diagnostics())

        def do_throw(self, *a):
            self.log(core.cmd_throw())

        def do_train(self, *a):
            n = self.inp.text.strip()
            arg = int(n) if n.isdigit() else 100
            self.inp.text = ""
            self.log(core.cmd_train(arg))
            self.refresh_status()

        def do_download(self, *a):
            n = self.inp.text.strip()
            arg = int(n) if n.isdigit() else 300
            self.inp.text = ""
            self.log(core.cmd_download(arg))
            self.refresh_status()

        def do_save(self, *a):
            ok = core.save()
            self.log("сохранено" if ok else "не удалось сохранить")

        def on_stop(self):
            core.save()

    IoApp().run()


def run_console():
    app = App()
    app.load()
    print("Мир Ио — монолит. Команды: прожить, тик, мир, статус, вопрос,")
    print("обучить, скачать, сон, диагностика, гипотеза, бросить, сохранить, выход")
    while True:
        try:
            line = input("ио> ").strip()
        except EOFError:
            break
        if not line:
            continue
        parts = line.split(maxsplit=1)
        cmd, arg = parts[0], parts[1] if len(parts) > 1 else ""
        if cmd == "выход":
            app.save()
            print("до встречи")
            break
        elif cmd == "прожить":
            app.cmd_live(int(arg) if arg.isdigit() else 1)
            print("прожито")
        elif cmd == "тик":
            print(app.cmd_tick())
        elif cmd == "мир":
            print(app.cmd_world())
        elif cmd == "статус":
            print(app.cmd_status())
        elif cmd == "вопрос":
            print(app.cmd_ask(arg))
        elif cmd == "обучить":
            print(app.cmd_train(int(arg) if arg.isdigit() else 100))
        elif cmd == "скачать":
            print(app.cmd_download(int(arg) if arg.isdigit() else 300))
        elif cmd == "сон":
            print(app.cmd_sleep())
        elif cmd == "диагностика":
            print(app.cmd_diagnostics())
        elif cmd == "гипотеза":
            print(app.cmd_hypothesis())
        elif cmd == "бросить":
            print(app.cmd_throw())
        elif cmd == "сохранить":
            app.save()
            print("сохранено")
        else:
            print("не знаю команду")


if __name__ == "__main__":
    if "--console" in sys.argv:
        run_console()
    else:
        import traceback
        try:
            core = App()
            core.load()
            run_kivy(core)
        except Exception:
            show_error(traceback.format_exc())
