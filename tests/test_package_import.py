def test_package_exposes_version() -> None:
    import foundlab

    assert foundlab.__version__ == "0.1.0"
