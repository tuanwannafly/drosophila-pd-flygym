class Interpolator:
    """Interpolation logic for frames."""

    @staticmethod
    def linear(a: float, b: float, t: float) -> float:
        return a + (b - a) * t

    @staticmethod
    def step(a: float, b: float, t: float) -> float:
        return a if t < 1.0 else b

    @staticmethod
    def cubic(a: float, b: float, t: float) -> float:
        return Interpolator.linear(a, b, t * t * (3 - 2 * t))
