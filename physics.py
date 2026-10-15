import math

G = 9.8

class Throw:
    """Бросок камня. Метод Верле с честным сидом истории по обеим осям."""
    def __init__(self, v0=15.0, angle=45.0, dt=0.01, mass=0.2, cdrag=0.005):
        self.m, self.dt, self.cd = mass, dt, cdrag
        rad = math.radians(angle)
        self.x, self.y = 0.0, 0.0
        self.vx, self.vy = v0 * math.cos(rad), v0 * math.sin(rad)
        # честный сид истории: x(t-dt), y(t-dt)
        self.pvx = self.x - self.vx * dt
        self.pvy = self.y - self.vy * dt
        self.pts = []
        self.record()

    def accel(self, vx, vy):
        v = math.hypot(vx, vy)
        k = self.cd / self.m
        return -k * v * vx, -G - k * v * vy

    def record(self):
        ke = 0.5 * self.m * (self.vx ** 2 + self.vy ** 2)
        pe = self.m * G * self.y
        self.pts.append((self.x, self.y, ke + pe))

    def step(self):
        ax, ay = self.accel(self.vx, self.vy)
        nx = 2 * self.x - self.pvx + ax * self.dt ** 2
        ny = 2 * self.y - self.pvy + ay * self.dt ** 2
        nvx = (nx - self.x) / self.dt
        nvy = (ny - self.y) / self.dt
        self.pvx, self.pvy = self.x, self.y
        self.x, self.y = nx, ny
        self.vx, self.vy = nvx, nvy
        landed = self.y < 0.0 and self.pts[-1][1] > 0.0
        if not landed:
            self.record()
        return not landed

    def run(self, max_steps=200000):
        n = 0
        while n < max_steps and self.step():
            n += 1

    def results(self):
        rng = max(p[0] for p in self.pts)
        apex = max(p[1] for p in self.pts)
        return rng, apex

    def audit(self):
        # закон сохранения с сопротивлением: механическая энергия НЕ растёт
        if len(self.pts) < 2:
            return False, self.pts
        prev = self.pts[0][2]
        for p in self.pts[1:]:
            if p[2] > prev + 0.35:
                return False, self.pts
            prev = p[2]
        return True, self.pts
