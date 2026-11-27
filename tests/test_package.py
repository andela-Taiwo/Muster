"""The package imports and says what version it is."""

import muster


def test_the_package_has_a_version() -> None:
    assert muster.__version__ == "0.1.0"


def test_the_package_is_typed() -> None:
    from importlib.resources import files

    assert files("muster").joinpath("py.typed").is_file()
