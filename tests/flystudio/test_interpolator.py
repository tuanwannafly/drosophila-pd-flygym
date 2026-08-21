from drosophila_pd.flystudio.interpolator import Interpolator

def test_interpolator():
    assert Interpolator.linear(0.0, 10.0, 0.5) == 5.0
    assert Interpolator.step(0.0, 10.0, 0.5) == 0.0
    assert Interpolator.step(0.0, 10.0, 1.0) == 10.0

    assert Interpolator.cubic(0.0, 10.0, 0.5) == 5.0
