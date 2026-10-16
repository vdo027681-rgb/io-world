import os, sys, traceback

_LOG_CANDIDATES = [
    '/storage/emulated/0/Download/io_crash.log',
    '/storage/emulated/0/io_crash.log',
    os.path.expanduser('~/io_crash.log'),
]

def _write_log(text):
    for p in _LOG_CANDIDATES:
        try:
            with open(p, 'a') as f:
                f.write(text)
            return p
        except Exception:
            pass
    return None

def _crash_hook(t, v, tb):
    text = ''.join(traceback.format_exception(t, v, tb))
    path = _write_log(text)
    try:
        from kivy.app import App
        from kivy.uix.label import Label
        class CrashApp(App):
            def build(self):
                return Label(text=(text + '\n\n(log: %s)' % str(path))[:4000])
        CrashApp().run()
        return
    except Exception:
        pass
    sys.__excepthook__(t, v, tb)

sys.excepthook = _crash_hook

"""
Мир Ио — расширенная версия.
Консоль: python main.py --console
Команды: прожить N, мир, статус, вопрос ..., обучить N, скачать N,
         сон, диагностика, гипотеза, бросить, сохранить, выход
"""
import os, sys, json, random

import planet
from planet import Planet, PLACES, LETTERS, FIELD
from physics import Throw
from mathmind import safe_calc, is_prime
from sciences import Science, correlation
from neurobrain import Brain
from subconscious import Subconscious, build_vocab
import world as W
import fetch_library

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE = os.path.join(HERE, "save.json")
SEED = os.path.join(HERE, "library", "seed.txt")


class App:
    def __init__(self):
        self.pl = Planet()
        self.soc = W.Society(self.pl)
        self.sci = Science()
        self.brain = Brain()
        self.sub = None
        self.counts = {}   # биграммы
        self.lemmas = []
        self._load_corpus()

    def _load_corpus(self):
        text = ""
        if os.path.exists(SEED):
            with open(SEED, "r", encoding="utf-8") as f:
                text = f.read()
        for fn in os.listdir(os.path.join(HERE, "library")):
            if fn.endswith(".txt") and fn != "seed.txt":
                with open(os.path.join(HERE, "library", fn), "r", encoding="utf-8") as f:
                    text += " " + f.read()
        self.text = text
        self.lemmas = build_vocab(text, min_count=1, limit=160)
        self.brain.wire_vocab(self.lemmas)
        self.sub = Subconscious(self.lemmas, lr=0.2)
        toks = [w for w in text.split() if w in self.sub.vidx]
        for a, b in zip(toks, toks[1:]):
            self.counts[(a, b)] = self.counts.get((a, b), 0) + 1

    # ---------- интеллект ----------
    def intelligence(self):
        b = self.pl.body
        logic = 40 + 10 * len(self.sci.hypotheses) + 5 * sum(
            1 for h in self.sci.hypotheses.values() if h.accepted)
        memory = 30 + min(50, len(self.lemmas) // 3)
        knowledge = 20 + min(60, len(self.sci.facts) * 10 + len(self.text) // 4000)
        wisdom = min(80, 10 * len(self.brain.assoc) + len(self.sci.facts) * 8)
        wit = 35 + min(45, len(self.counts) // 50)
        return {"логика": min(100, logic), "память": min(100, memory),
                "знание": min(100, knowledge), "мудрость": max(0, min(100, wisdom)),
                "сообразительность": min(100, wit)}

    # ---------- сохранить / загрузить ----------
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
        with open(SAVE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def load(self):
        if not os.path.exists(SAVE):
            return False
        with open(SAVE, "r", encoding="utf-8") as f:
            d = json.load(f)
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

    # ---------- команды ----------
    def cmd_live(self, n=1):
        for _ in range(n):
            while self.pl.tick > 0 or len(getattr(self.soc, "_plan", []) or []) == 0:
                self.pl.step()
                self.soc.step()
                if self.pl.tick == 0:
                    break
            self.soc.midnight()

    def cmd_world(self):
        return W.map_view(self.pl, self.soc)

    def cmd_status(self):
        b = self.pl.body
        intel = self.intelligence()
        return ("день %d, %s, облачность %.2f, температура %.1f C\n"
                "монеты %d, энергия %.0f, настроение: %s\n"
                "лемм %d, биграмм %d, фактов %d, дел сегодня: %s\n"
                "интеллект: %s" % (
                    self.pl.day, self.pl.clock(), self.pl.cloud,
                    self.pl.temperature(), b.coins, b.energy, self.soc.mood,
                    len(self.lemmas), len(self.counts), len(self.sci.facts),
                    self.soc.task_done_today and "выполнено" or "ожидается",
                    ", ".join("%s %d" % (k, v) for k, v in intel.items())))

    def cmd_ask(self, q):
        ans = self.sub.answer(q)
        # мозг подсказывает ассоциации
        words = q.split()
        for w in words:
            tgt = [b for (a, b) in self.brain.assoc if a == w]
            if tgt:
                ans += " | " + " ".join(tgt)
        return ans

    def cmd_train(self, n=100):
        toks = [w for w in self.text.split() if w in self.sub.vidx]
        loss0 = None
        loss = None
        if len(toks) < 3:
            return "корпус пуст"
        rng = random.Random(9)
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
        path = fetch_library.download("вертер", max_chars=max(1, int(chars)) * 1000)
        if path is None:
            return "источник не найден"
        self._load_corpus()
        return "скачано: %s, лемм теперь %d" % (os.path.basename(path), len(self.lemmas))

    def cmd_sleep(self):
        words = self.brain.dream_step()
        return "сон шепчет: " + " ".join(words[:8])

    def cmd_diagnostics(self):
        # честный lesion-экзамен: обучаем ассоциации, экзаменуем, поражаем, экзаменуем
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
        ok, pts = phys.audit()
        rng, apex = phys.results()
        return ("экзамен до поражения: %s; после: %s\n"
                "бросок: дальность %.2f м, апекс %.2f м, закон %s" % (
                    before, after, rng, apex,
                    "соблюдён" if ok else "нарушен"))

    def cmd_hypothesis(self):
        h = self.sci.propose("еда растёт от солнца", 0.7)
        xs = [s for s, g in self.soc.food_log]
        ys = [g for s, g in self.soc.food_log]
        if len(xs) < 3:
            return "мало данных: %d дней" % len(xs)
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


def run_console():
    app = App()
    app.load()
    print("Мир Ио — расширенная версия. Команды: прожить, мир, статус, вопрос,")
    print("обучить, скачать, сон, диагностика, гипотеза, бросить, сохранить, выход")
    while True:
        try:
            line = input("ио> ").strip()
        except EOFError:
            break
        if not line:
            continue
        parts = line.split(maxsplit=1)
        cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else ""
        if cmd == "выход":
            app.save()
            print("до встречи")
            break
        elif cmd == "прожить":
            app.cmd_live(int(arg) if arg.isdigit() else 1)
            print("прожито")
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


# ---------- Kivy-версия ----------
def run_kivy():
    from kivy.app import App as KApp
    from kivy.uix.label import Label

    class IoApp(KApp):
        def build(self):
            return Label(text="Ио\nкорпорация Ио")

    IoApp().run()


if __name__ == "__main__":
    if "--console" in sys.argv:
        run_console()
    else:
        try:
            run_kivy()
        except ImportError:
            run_console()
