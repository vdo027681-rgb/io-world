import math, random

DAY = 48              # тиков в сутках (1 тик = 30 минут)
EARTH_R = 6371.0      # радиус Земли, км
LAT, LON = 55.675, 37.817   # Горки Ленинские
GRID = 51             # регион 51x51 км

PLACES = {
    "дом": (24, 24),
    "корпорация Ио": (12, 10),
    "магазин": (38, 30),
    "библиотека": (18, 40),
    "парк": (40, 12),
}
LETTERS = {"дом": "Д", "корпорация Ио": "Р", "магазин": "М",
           "библиотека": "Б", "парк": "П"}

FIELD = [(x, y) for x in range(5, 15) for y in range(5, 15)]


class Body:
    """Тело Ио: деньги, энергия, ходьба."""
    def __init__(self):
        self.x, self.y = 24.0, 24.0
        self.coins = 2
        self.energy = 100.0
        self.hunger = 0.0

    def walk(self, tx, ty):
        dx, dy = tx - self.x, ty - self.y
        d = math.hypot(dx, dy)
        if d < 0.35:
            self.x, self.y = tx, ty
            return True
        step = min(d, 1.5)
        self.x += dx / d * step
        self.y += dy / d * step
        self.energy = max(0.0, self.energy - 0.12)
        return False


class Planet:
    """Планета: время, солнце, единый термометр, поля еды."""
    def __init__(self, seed=7):
        self.rng = random.Random(seed)
        self.tick = 0
        self.day = 1
        self.cloud = 0.35
        self.body = Body()
        self.food = {}

    def step(self):
        self.tick += 1
        if self.tick >= DAY:
            self.tick = 0
            self.day += 1
            self.cloud = min(1.0, max(0.05, self.rng.gauss(0.4, 0.25)))
        s = self.sunlight()
        for c in FIELD:
            self.food[c] = self.food.get(c, 0.0) + 0.05 * s

    def sun_elevation(self):
        return math.sin(math.pi * self.tick / DAY)

    def sunlight(self):
        e = self.sun_elevation()
        return max(0.0, e) * (1.0 - self.cloud)

    def temperature(self):
        # единый термометр: полночь ~2 C, полдень ~20 C (май)
        return 11.0 + 9.0 * self.sun_elevation()

    def clock(self):
        h = int(self.tick * 24 // DAY)
        m = int((self.tick * 24 * 60 // DAY) % 60)
        return "%02d:%02d" % (h, m)
