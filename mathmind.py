import math

def safe_calc(expr):
    """Безопасная арифметика: только цифры и знаки."""
    allowed = set("0123456789+-*/(). ")
    if not expr or not set(expr) <= allowed:
        return None
    try:
        return eval(expr, {"__builtins__": {}}, {})
    except Exception:
        return None

def is_prime(n):
    if n < 2 or int(n) != n:
        return False
    n = int(n)
    if n % 2 == 0:
        return n == 2
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True

def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0

def stats(xs):
    if not xs:
        return (0.0, 0.0)
    m = mean(xs)
    var = sum((x - m) ** 2 for x in xs) / len(xs)
    return (m, math.sqrt(var))
