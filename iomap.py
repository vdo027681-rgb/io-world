"""Карта мира Ио: сетка 51x51, поле еды, места и точка Ио."""
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from planet import PLACES, LETTERS, GRID

PLACE_COLORS = {
    "дом": (0.85, 0.65, 0.25),
    "корпорация Ио": (0.85, 0.3, 0.3),
    "магазин": (0.3, 0.55, 0.9),
    "библиотека": (0.6, 0.35, 0.85),
    "парк": (0.3, 0.75, 0.4),
}


class MapWidget(Widget):
    """Рисует мир Ио и обновляется раз в секунду."""

    def __init__(self, core, **kw):
        super(MapWidget, self).__init__(**kw)
        self.core = core
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
        c = min(w, h) / float(GRID)
        ox = self.x + (w - c * GRID) / 2.0
        oy = self.y + (h - c * GRID) / 2.0
        pl = self.core.pl
        sun = pl.sunlight()

        self.canvas.clear()
        with self.canvas:
            # фон: от тёмной ночи к дневному небу
            Color(0.04 + 0.30 * sun, 0.05 + 0.30 * sun, 0.10 + 0.25 * sun)
            Rectangle(pos=self.pos, size=self.size)

            # поле еды (квадрат 5..14): яркость = запас еды
            maxf = max(pl.food.values()) if pl.food else 0.0
            for (gx, gy), val in pl.food.items():
                if val <= 0:
                    continue
                a = min(1.0, val / maxf) if maxf > 0 else 0.0
                Color(0.10 + 0.25 * a, 0.15 + 0.55 * a, 0.12)
                Rectangle(pos=(ox + gx * c, oy + gy * c), size=(c, c))
            Color(0.25, 0.55, 0.25, 0.9)
            Line(rectangle=(ox + 5 * c, oy + 5 * c, 10 * c, 10 * c), width=1.5)

            # места
            for name, (px, py) in PLACES.items():
                Color(*PLACE_COLORS[name])
                Rectangle(pos=(ox + (px - 1.5) * c, oy + (py - 1.5) * c),
                          size=(3 * c, 3 * c))

            # точка Ио
            Color(1.0, 0.9, 0.2)
            r = max(5.0, 1.6 * c)
            Ellipse(pos=(ox + pl.body.x * c - r / 2.0,
                         oy + pl.body.y * c - r / 2.0), size=(r, r))

        # подписи мест
        for name, lab in self._labs.items():
            px, py = PLACES[name]
            lab.pos = (ox + px * c - lab.width / 2.0,
                       oy + py * c - lab.height / 2.0)
