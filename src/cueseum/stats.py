import numpy as np
import pandas as pd


def bootstrap_ci(values, n=2000, seed=0, alpha=0.05, stat=np.mean):
    values = np.asarray(values)
    rng = np.random.default_rng(seed)
    boots = [stat(values[rng.integers(0, len(values), len(values))]) for _ in range(n)]
    return float(stat(values)), *np.quantile(boots, [alpha / 2, 1 - alpha / 2]).tolist()


def select_max(table):
    return lambda keys: table.columns[np.argmax(table.loc[keys].mean().to_numpy())]


def grouped_cv_select_score(table, groups, select_fn, folds=2, repeats=50, seed=0):
    if set(groups.index) != set(table.index):
        raise ValueError("groups must cover exactly the table's problems")
    rng = np.random.default_rng(seed)
    out = pd.DataFrame(np.nan, index=range(repeats), columns=table.index)
    members = [np.asarray(keys) for keys in groups.groupby(groups).groups.values()]
    for r in range(repeats):
        for keys in members:
            parts = np.array_split(rng.permutation(keys), folds)
            for i, held in enumerate(parts):
                cue = select_fn(np.concatenate(parts[:i] + parts[i + 1:]))
                out.loc[r, held] = table.loc[held, cue].to_numpy()
    return out


def permutation_null(table, groups, select_fn, n=200, seed=0, **cv):
    rng = np.random.default_rng(seed)
    return np.array([
        grouped_cv_select_score(table, pd.Series(rng.permutation(groups.to_numpy()), index=groups.index),
                                select_fn, seed=seed + 1 + i, **cv).to_numpy().mean()
        for i in range(n)])


def p_value(observed, null):
    return float((1 + np.sum(np.asarray(null) >= observed)) / (1 + len(null)))
