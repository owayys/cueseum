import numpy as np
import pandas as pd
import pytest

from cueseum import stats

KEYS = [f"p{i}" for i in range(20)]
GROUPS = pd.Series(["a"] * 10 + ["b"] * 10, index=KEYS)
TABLE = pd.DataFrame({"x": [1.0] * 10 + [0.0] * 10, "y": [0.0] * 10 + [0.9] * 10}, index=KEYS)


def test_bootstrap_ci():
    assert stats.bootstrap_ci([0.5] * 10) == (0.5, 0.5, 0.5)
    m, lo, hi = stats.bootstrap_ci(np.arange(100.0))
    assert lo < m < hi


def test_select_max_ties_take_first_column():
    t = pd.DataFrame({"x": [1.0], "y": [1.0]}, index=["p"])
    assert stats.select_max(t)(["p"]) == "x"


def test_grouped_cv_beats_global():
    sel = stats.select_max(TABLE)
    grouped = stats.grouped_cv_select_score(TABLE, GROUPS, sel, repeats=3)
    single = stats.grouped_cv_select_score(TABLE, pd.Series("g", index=KEYS), sel, repeats=3)
    assert grouped.shape == (3, 20) and not grouped.isna().any().any()
    assert grouped.to_numpy().mean() == 0.95
    assert single.to_numpy().mean() < 0.95


def test_permutation_null():
    sel = stats.select_max(TABLE)
    null = stats.permutation_null(TABLE, GROUPS, sel, n=20, repeats=2)
    assert null.shape == (20,)
    assert stats.p_value(0.95, null) < 0.2
    assert stats.p_value(-1, null) == 1.0


def test_grouped_cv_rejects_partial_groups():
    with pytest.raises(ValueError):
        stats.grouped_cv_select_score(TABLE, GROUPS[:10], stats.select_max(TABLE))
