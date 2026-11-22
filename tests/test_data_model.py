from repro360.data import feature_target, load_fertility


def test_fertility_shape():
    df = load_fertility()
    assert len(df) == 100


def test_fertility_class_balance_documented():
    df = load_fertility()
    assert (df["diagnosis"] == "O").sum() == 12


def test_feature_target_split():
    df = load_fertility()
    X, y = feature_target(df)
    assert X.shape == (100, 9)
    assert set(y.unique()) == {0, 1}


def test_sitting_hours_denormalized_with_assumption():
    df = load_fertility()
    assert df["sitting_hours_denorm"].max() <= 16.0
