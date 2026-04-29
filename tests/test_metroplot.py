import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from metroplot import Diagram, Line, Station


def _basic():
    return (Diagram()
            .station("a", 0, 0, "A")
            .station("b", 2, 0, "B")
            .station("c", 2, -2, "C", label_pos="below"))


def test_builder_chaining_returns_self():
    d = Diagram()
    assert d.station("a", 0, 0) is d
    assert d.line("l", "#000", [["a"]]) is d


def test_stations_and_lines_recorded():
    d = _basic().line("main", "#111", [["a", "b", "c"]])
    assert set(d.stations) == {"a", "b", "c"}
    assert isinstance(d.stations["a"], Station)
    assert len(d.lines) == 1
    assert isinstance(d.lines[0], Line)
    assert d.lines[0].routes == [["a", "b", "c"]]


def test_render_creates_one_circle_per_station():
    d = _basic().line("main", "#111", [["a", "b", "c"]])
    ax = d.render()
    circles = [p for p in ax.patches if isinstance(p, Circle)]
    assert len(circles) == 3
    plt.close("all")


def test_split_routes_share_a_station():
    d = (_basic()
         .station("d", 4, 0, "D")
         .line("split", "#e07a6b", [["a", "b", "c"], ["b", "d"]]))
    ax = d.render()
    lines = ax.get_lines()
    # 2 segments for first route + 1 for the branch = 3 drawn segments
    # (vertical/horizontal hops for the L-bend on a→c-via-b are split into 2 plot calls)
    assert len(lines) >= 3
    plt.close("all")


def test_shared_segment_uses_parallel_tracks():
    """Two lines on the same a-b segment should be drawn at distinct y offsets."""
    d = (Diagram()
         .station("a", 0, 0, "A")
         .station("b", 3, 0, "B")
         .line("l1", "#1f2a44", [["a", "b"]])
         .line("l2", "#e07a6b", [["a", "b"]]))
    ax = d.render()
    # Both segments are horizontal: each is one Line2D with constant y.
    horizontals = [ln for ln in ax.get_lines() if ln.get_ydata()[0] == ln.get_ydata()[-1]]
    ys = sorted({ln.get_ydata()[0] for ln in horizontals})
    assert len(ys) == 2, f"expected 2 distinct y offsets, got {ys}"
    assert ys[1] - ys[0] > 0
    plt.close("all")


def test_lone_segment_has_zero_offset():
    d = (Diagram()
         .station("a", 0, 0)
         .station("b", 3, 0)
         .line("solo", "#000", [["a", "b"]]))
    ax = d.render()
    horizontals = [ln for ln in ax.get_lines()]
    assert horizontals[0].get_ydata()[0] == 0
    plt.close("all")


def test_bend_hv_vs_vh_corner_differs():
    stations = lambda: (Diagram()
                        .station("a", 0, 0)
                        .station("b", 3, -2))
    ax_hv = stations().line("l", "#000", [["a", "b"]], bend="hv").render()
    ax_vh = stations().line("l", "#000", [["a", "b"]], bend="vh").render()
    # hv corner is at (3, 0); vh corner is at (0, -2). Verify by checking
    # whether any plotted segment hits y=-2 at x=0 (vh) vs x=3 (hv).
    def corners(ax):
        return [(ln.get_xdata()[0], ln.get_ydata()[0],
                 ln.get_xdata()[-1], ln.get_ydata()[-1]) for ln in ax.get_lines()]
    assert corners(ax_hv) != corners(ax_vh)
    plt.close("all")
