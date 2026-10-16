"""
Мир Ио — расширенная версия.
Консоль: python main.py --console
Графика: python main.py
Команды: прожить N, тик, мир, статус, вопрос ..., обучить N, скачать N,
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

    # ---------- один шаг мира ----------
    def _step_once(self):
        """Один тик: план дня, шаг планеты, шаг общества; на границе суток — midnight."""
        if not getattr(self.soc, "_plan", None):
            self.soc._plan = self.soc.plan_day()
        self.pl.step()
        self.soc.step()
        if self.pl.tick == 0:
            self.soc.midnight()
            self.soc._plan = None

    # ---------- команды ----------
    def cmd_tick(self):
        self._step_once()
        b = self.pl.body
        act = "?"
        plan = getattr(self.soc, "_plan", None)
        if plan and len(plan) > 0:
            act = {"дом": "дома", "корпорация Ио": "на работе",
                   "магазин": "в магазине"}.get(plan[0], plan[0])
        return ("день %d, %s — Ио %s, монеты %d, энергия %.0f" % (
            self.pl.day, self.pl.clock(), act, b.coins, b.energy))

    def cmd_live(self, n=1):
        for _ in range(n):
            for _ in range(48):
                self._step_once()
            self.soc.midnight()
            self.soc._plan = None

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

    def cmd_diary(self, n=10):
        if not self.soc.diary_all:
            return "дневник пуст"
        entries = self.soc.diary_all[-n:]
        return "\n".join(str(e[1]) if len(e) > 1 else str(e) for e in entries)


def run_console():
    app = App()
    app.load()
    print("Мир Ио — расширенная версия. Команды: прожить, тик, мир, статус, вопрос,")
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


# ---------- Kivy-версия ----------
def run_kivy():
    from kivy.app import App as KApp
    from kivy.core.window import Window
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.label import Label
    from kivy.uix.button import Button
    from kivy.uix.textinput import TextInput
    from kivy.uix.scrollview import ScrollView
    from iomap import MapWidget

    core = App()
    core.load()

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

        # ---------- служебное ----------
        def log(self, text):
            self.log_lines.append(text)
            self.log_lines = self.log_lines[-60:]
            self.out.text = "\n\n".join(self.log_lines)

        def refresh_status(self):
            self.status.text = core.cmd_status()

        def diary_tail(self):
            try:
                d = core.cmd_diary(3)
            except Exception:
                d = ""
            if d and d != "дневник пуст":
                return "\n--- дневник ---\n" + d
            return ""

        # ---------- кнопки ----------
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
            self.log("сохранено" if ok else "не удалось сохранить (нет доступа к записи)")

        def on_stop(self):
            core.save()

    IoApp().run()


if __name__ == "__main__":
    if "--console" in sys.argv:
        run_console()
    else:
        try:
            run_kivy()
        except ImportError:
            run_console()
