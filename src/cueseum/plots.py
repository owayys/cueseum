import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def style():
    plt.rcParams.update({"figure.dpi": 150, "font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3})


def save(fig, path):
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
