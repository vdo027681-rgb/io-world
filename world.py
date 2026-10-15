import math
import planet
from planet import Planet, PLACES, LETTERS, FIELD, DAY


class Society:
    """Общество Ио: корпорация Ио, распорядок, магазин, дела."""

    TASKS = ["помочь соседу с починкой", "полить цветы у подъезда",
             "отнести посылку", "накормить кота соседа",
             "помыть окна в библиотеке", "разобрать коробки на складе"]

    def __init__(self, pl):
        self.pl = pl
        self.task = self.TASKS[0]
        self.task_done_today = False
        self.worked_today = False
        self.bought_today = False
        self.eaten_today = False
        self.mood = "спокойствие"
        self.diary_all = []      # все записи с номером дня
        self.sun_sum = 0.0
        self.sun_n = 0
        self.food_prev = None
        self.food_log = []       # (средний свет за день, прирост еды)
        self._prev_food = 0.0

    def plan_day(self):
        # 48 тиков: дом(14) -> путь и работа(20) -> дело(4) -> магазин(2) -> дом(8)
        return (["дом"] * 14 + ["корпорация Ио"] * 20 +
                ["дело"] * 4 + ["магазин"] * 2 + ["дом"] * 8)

    def step(self):
        pl = self.pl
        plan = getattr(self, "_plan", None)
        if plan is None or len(plan) <= 0:
            self._plan = plan = self.plan_day()
        act = plan[0]
        self._plan = plan[1:]

        b = pl.body
        if act == "дело":
            if not self.task_done_today:
                self.task_done_today = True
                self.diary("Ио выполнил дело — " + self.task)
                self.mood = "гордость"
        elif act in PLACES:
            tx, ty = PLACES[act]
            if b.walk(tx, ty):
                if act == "корпорация Ио" and not self.worked_today:
                    if 21 <= pl.tick < 39:        # окно 10:48 - 19:12
                        b.coins += 3
                        self.worked_today = True
                        self.diary("Ио отработал смену в корпорации Ио: +3 монет")
                        self.mood = "радость"
                elif act == "магазин" and not self.bought_today:
                    if b.coins >= 2:
                        b.coins -= 2
                        self.bought_today = True
                        self.diary("Ио купил еды в магазине")
        elif act == "дом":
            if not self.eaten_today and pl.tick >= 26:
                self.eaten_today = True
                b.energy = min(100.0, b.energy + 15.0)
                self.diary("Ио дома, отдыхает")
        self.sun_sum += pl.sunlight()
        self.sun_n += 1

    def midnight(self):
        """Конец суток: записи, новая задача."""
        b = self.pl.body
        self.diary("Конец дня %d" % self.pl.day)
        if self._prev_food is not None:
            here = FIELD[0]
            gain = self.pl.food.get(here, 0.0) - self._prev_food
            avg_sun = self.sun_sum / max(1, self.sun_n)
            self.food_log.append((avg_sun, gain))
        self._prev_food = self.pl.food.get(FIELD[0], 0.0)
        self.sun_sum, self.sun_n = 0.0, 0.0
        self.worked_today = False
        self.task_done_today = False
        self.bought_today = False
        self.eaten_today = False
        idx = self.pl.day % len(self.TASKS)
        self.task = self.TASKS[idx]
        self.mood = "спокойствие"

    def diary(self, text):
        self.diary_all.append((self.pl.day, text))

    def diary_today(self):
        return [(d, t) for (d, t) in self.diary_all if d == self.pl.day]


def map_view(pl, soc, half=18):
    """Текстовая карта: окно на весь город"""
    b = pl.body
    cx, cy = 25, 25
    rows = []
    for j in range(cy - half, cy + half + 1):
        row = []
        for i in range(cx - half, cx + half + 1):
            ch = "."
            if (i, j) in pl.food and pl.food[(i, j)] > 0.5:
                ch = "Т"
            for name, (px, py) in PLACES.items():
                if int(px) == i and int(py) == j:
                    ch = LETTERS[name]
            if int(b.x) == i and int(b.y) == j:
                ch = "И"
            row.append(ch)
        rows.append(" ".join(row))
    return "\n".join(rows)
