import matplotlib.pyplot as plt

from cueseum import plots


def test_save(tmp_path):
    plots.style()
    fig, ax = plt.subplots()
    ax.plot([0, 1])
    plots.save(fig, tmp_path / "f.png")
    assert (tmp_path / "f.png").stat().st_size > 0
