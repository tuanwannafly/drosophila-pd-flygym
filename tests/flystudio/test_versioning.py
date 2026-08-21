from drosophila_pd.flystudio.versioning import Version

def test_version():
    v = Version(1, 2, 3)
    assert str(v) == "1.2.3"

    v2 = Version.from_string("2.0.1")
    assert v2.major == 2
    assert v2.minor == 0
    assert v2.patch == 1

    v3 = Version.from_string("invalid")
    assert v3.major == 1
