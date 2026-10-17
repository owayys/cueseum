import json
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from matplotlib.colors import LinearSegmentedColormap
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

from cueseum import cuesets, plots, stats
from cueseum.paths import commit, experiment_dir, upstream_commit
from cueseum.problems import read_jsonl
from cueseum.rollouts import load_cells

E = experiment_dir("e01_cue_tree")
CFG = yaml.safe_load((E / "config.yaml").read_text())
LEVELS = {"subject": ["capability"], "level": ["level"], "subject_x_level": ["capability", "level"]}
PARENTS = {"subject": "global", "level": "global", "subject_x_level": "subject"}
GUARD, FOLDS, REPEATS, SHUFFLES, BOOT, SEED = 0.10, 2, 50, 200, 2000, 0
RAMP = LinearSegmentedColormap.from_list("blue", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
INK, MUTED, SURFACE = "#0b0b0b", "#898781", "#fcfcfb"


def answer_type(gt):
    s = gt.strip().strip("$").replace(" ", "")
    if re.fullmatch(r"-?\d+", s):
        return "integer"
    if re.fullmatch(r"-?\\d?frac\{-?\d+\}\{\d+\}|-?\d+/\d+", s):
        return "fraction"
    if re.search(r"[a-zA-Z\\]", s) and not re.search(r"\\text|[,()\[\]]", s):
        return "expression"
    return "other"


def entropy(keys):
    p = keys.fillna("NONE").value_counts(normalize=True).to_numpy()
    return float(-(p * np.log2(p)).sum())


def tables(df, order, rollouts):
    d = df[df.rollout_index.isin(rollouts)]
    g = d.groupby(["problem_key", "cue"])
    acc = g.correct.mean().unstack()[order]
    ent = g.answer_key.apply(entropy).unstack()[order]
    none = (1 - g.committed.mean()).unstack()[order]
    return acc, ent, none


def select_entropy(ent, none):
    e, n, index, cols = ent.to_numpy(), none.to_numpy(), ent.index, ent.columns

    def select(keys):
        idx = index.get_indexer(keys)
        me, mn = e[idx].mean(axis=0), n[idx].mean(axis=0)
        ok = mn <= mn[0] + GUARD
        ok[0] = False
        return cols[np.argmin(np.where(ok, me, np.inf))] if ok.any() else cols[0]
    return select


def boot(x):
    m, lo, hi = stats.bootstrap_ci(np.asarray(x, float), n=BOOT, seed=SEED)
    return {"mean": m, "lo": lo, "hi": hi}


def rollout_split(a, b, select_a, keys):
    per = pd.Series({k: select_a([k]) for k in keys})
    glob = select_a(keys)
    held = np.array([b.at[k, per[k]] for k in keys])
    held_g = b.loc[keys, glob].to_numpy()
    ins = np.array([a.at[k, per[k]] for k in keys]) - a.loc[keys, glob].to_numpy()
    top = a.loc[keys].to_numpy()
    return {"n": len(keys), "global_cue": glob, "per_problem": boot(held), "global": boot(held_g),
            "diff": boot(held - held_g), "in_sample_diff_labeled": boot(ins),
            "tie_rate": float(((top == top.max(axis=1, keepdims=True)).sum(axis=1) > 1).mean())}


def levels(acc, groups_by, select_of, keys):
    out, base = {}, None
    for name, cols in {"global": [], **LEVELS}.items():
        g = groups_by(cols).loc[keys]
        ok = g.map(g.value_counts()) >= FOLDS
        k = list(g.index[ok])
        if not k:
            out[name] = {"n": 0}
            continue
        sel = select_of(k)
        held = stats.grouped_cv_select_score(acc.loc[k], g.loc[k], sel, FOLDS, REPEATS, SEED).mean()
        glob = stats.grouped_cv_select_score(acc.loc[k], pd.Series("all", index=k), sel, FOLDS, REPEATS, SEED).mean()
        row = {"n": len(k), "groups": int(g.loc[k].nunique()), "held_out": boot(held), "diff_vs_global": boot(held - glob)}
        if name != "global":
            null = stats.permutation_null(acc.loc[k], g.loc[k], sel, SHUFFLES, SEED, folds=FOLDS, repeats=REPEATS)
            row |= {"null_mean": float(null.mean()), "null_sd": float(null.std()), "p": stats.p_value(held.mean(), null)}
        out[name] = row
    return out


def clusters(acc, a, b, labels, keys, out):
    def profile(t):
        p = t.loc[keys].sub(t.loc[keys].mean(axis=1), axis=0)
        return p[p.std(axis=1) > 0]

    p = profile(acc)
    z = linkage(p.to_numpy(), method="average", metric="correlation")
    fig, ax = plt.subplots(figsize=(10, 4), facecolor=SURFACE)
    with plt.rc_context({"lines.linewidth": 0.5}):
        dendrogram(z, ax=ax, no_labels=True, color_threshold=0, above_threshold_color=INK)
    ax.set(title="Cue-profile clustering, informative problems", ylabel="correlation distance")
    plots.save(fig, out / "dendrogram.png")
    res = {"n": len(p), "dropped_constant": len(keys) - len(p)}
    pa, pb = profile(a), profile(b)
    both = pa.index.intersection(pb.index)
    za, zb = (linkage(x.loc[both].to_numpy(), method="average", metric="correlation") for x in (pa, pb))
    for k in (5, 7):
        cut = fcluster(z, k, "maxclust")
        res[f"k{k}"] = {name: {"ari": adjusted_rand_score(lab.loc[p.index], cut),
                               "nmi": normalized_mutual_info_score(lab.loc[p.index], cut)} for name, lab in labels.items()}
        res[f"k{k}"]["stability_ari_0to3_vs_4to7"] = adjusted_rand_score(fcluster(za, k, "maxclust"), fcluster(zb, k, "maxclust"))
    res["stability_n"] = len(both)
    return res


def heatmap(t, groups, names, title, path):
    m = t.groupby(groups).mean().T
    m.rename(index=names).to_csv(path.with_suffix(".csv"))
    fig, ax = plt.subplots(figsize=(max(6, 0.32 * m.shape[1] + 3), 0.3 * len(m) + 1.5), facecolor=SURFACE)
    im = ax.imshow(m.to_numpy(), cmap=RAMP, vmin=0, vmax=1, aspect="auto")
    ax.set_yticks(range(len(m)), [names[c] for c in m.index])
    ax.set_xticks(range(m.shape[1]), [str(c) for c in m.columns], rotation=90)
    ax.grid(False)
    ax.set_title(title, color=INK)
    fig.colorbar(im, ax=ax, label="accuracy, rollouts 4–7")
    plots.save(fig, path)


def winners(acc, groups_by, keys):
    win = {"global": {"all": stats.select_max(acc)(keys)}}
    for name, cols in LEVELS.items():
        g = groups_by(cols).loc[keys]
        win[name] = {str(k): stats.select_max(acc)(list(v)) for k, v in g.groupby(g).groups.items()}
    change = {}
    for name, parent in PARENTS.items():
        pw = win[parent]
        child_parent = (lambda k: "all") if parent == "global" else (lambda k: k.split("|")[0])
        change[name] = float(np.mean([w != pw[child_parent(k)] for k, w in win[name].items()]))
    return win, change


def run(df, problems, cues, out):
    out.mkdir(parents=True, exist_ok=True)
    names = {"": "none", **{v: k for k, v in cues.items()}}
    order = ["none", *cues]
    df = df.assign(cue=df.cue.map(names))
    counts = df.groupby(["cue", "problem_key"]).rollout_index.apply(lambda r: sorted(r) == list(range(8)))
    assert len(counts) == len(order) * len(problems) and counts.all(), "every (cue, problem) needs rollouts 0-7"
    meta = problems.set_index("problem_key").loc[sorted(problems.problem_key)]
    groups_by = lambda cols: meta[cols].astype(str).agg("|".join, axis=1) if cols else pd.Series("all", index=meta.index)
    acc, ent, none = tables(df, order, range(8))
    a, ent_a, none_a = tables(df, order, range(4))
    b = tables(df, order, range(4, 8))[0]
    every = list(acc.index)
    informative = list(acc.index[~((acc == 0).all(axis=1) | (acc == 1).all(axis=1))])
    labels = {"subject": meta["capability"], "level": meta["level"], "answer_type": meta["gt"].map(answer_type)}
    res = {"problems": len(every), "n_informative": len(informative)}
    for sname, keys in {"all": every, "informative": informative}.items():
        res[sname] = {
            "5a": rollout_split(a, b, stats.select_max(a), keys),
            "5b_5c": levels(acc, groups_by, lambda k: stats.select_max(acc.loc[k]), keys),
            "5e_5a": rollout_split(a, b, select_entropy(ent_a, none_a), keys),
            "5e_5b_5c": levels(acc, groups_by, lambda k: select_entropy(ent.loc[k], none.loc[k]), keys),
        }
    res["5d"] = clusters(acc, a, b, labels, informative, out)
    res["5f_winners"], res["5f_winner_change_vs_parent"] = winners(acc, groups_by, every)
    plots.style()
    shown = {v: repr(k) if k else "no cue" for k, v in names.items()}
    heatmap(b, meta["capability"], shown, "Cue accuracy by subject (rollouts 4–7)", out / "heatmap_subject.png")
    heatmap(b, groups_by(LEVELS["subject_x_level"]), shown, "Cue accuracy by subject × level (rollouts 4–7)", out / "heatmap_subject_x_level.png")
    res["decision"] = decide(res["all"])
    return res


def decide(r):
    lo = lambda lv: r["5b_5c"][lv].get("diff_vs_global", {}).get("lo", -1)
    wins = lambda lv: lo(lv) > 0 and r["5b_5c"][lv]["p"] < 0.05
    per_problem = r["5a"]["diff"]["lo"] > 0
    if (wins("subject") or wins("level")) and per_problem:
        return "H1 supported"
    if per_problem:
        return "Partial"
    if not any(lo(lv) > 0 for lv in LEVELS):
        return "Not supported"
    return "Unclassified by rule; see REPORT"


if __name__ == "__main__":
    root, out = Path(sys.argv[1]), Path(sys.argv[2])
    problems = pd.DataFrame(read_jsonl(E / "data" / "tree_problems.jsonl"))
    if len(sys.argv) > 3:
        problems = pd.DataFrame(read_jsonl(sys.argv[3]))
    cues = cuesets.load(E / "data" / "tree_cues.json")
    res = run(load_cells(root), problems, cues, out)
    res["provenance"] = {"cueseum_commit": commit(), "upstream_commit": upstream_commit(), "model": CFG["model_hub"],
                         "revision": CFG["model_revision"], "prompt": CFG["prompt"], "temperature": CFG["temperature"],
                         "top_p": CFG["top_p"], "max_new_tokens": CFG["max_new_tokens"], "n_rollouts": CFG["n_rollouts"],
                         "sampling_seed": CFG["seed"], "analysis_seed": SEED, "folds": FOLDS, "repeats": REPEATS,
                         "shuffles": SHUFFLES, "bootstrap": BOOT, "guard": GUARD}
    (out / "summary.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(json.dumps({k: res[k] for k in ("problems", "n_informative", "decision")}))
