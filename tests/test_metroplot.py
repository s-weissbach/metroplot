import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, PathPatch

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
    # Default light theme: station_dot=False, so one circle per station.
    n_stations = len(d.stations)
    assert len(circles) == n_stations
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


def test_duplicate_station_coords_raise():
    d = (Diagram()
         .station("a", 1, 1, "A")
         .station("b", 1, 1, "B")
         .line("solo", "#000", [["a", "b"]]))
    import pytest
    with pytest.raises(ValueError, match="share coordinates"):
        d.render()
    plt.close("all")


def test_close_stations_warn():
    d = (Diagram()
         .station("a", 0, 0, "A")
         .station("b", 0.1, 0, "B")  # well within 2 * default radius
         .line("solo", "#000", [["a", "b"]]))
    import warnings as _w
    with _w.catch_warnings(record=True) as caught:
        _w.simplefilter("always")
        d.render()
    assert any("closer than" in str(w.message) for w in caught)
    plt.close("all")


def test_station_radius_auto_grows_for_many_lines():
    """With many parallel lines, the rendered circle should be bigger than
    the user-specified station_radius so line endpoints stay hidden."""
    # station_interchange_rect=False forces circles so we can read the radius.
    d = Diagram(station_radius=0.10, track_spacing=0.20, station_interchange_rect=False)
    d.station("a", 0, 0).station("b", 5, 0)
    for i in range(5):
        d.line(f"L{i}", "#000", [["a", "b"]])
    ax = d.render()
    radii = [p.get_radius() for p in ax.patches if isinstance(p, Circle)]
    # 5 lines, spacing 0.20 -> max_offset = 0.40 -> required >= sqrt(2) * 0.40 ~= 0.566
    assert radii[0] > 0.10
    assert radii[0] >= 0.40 * 1.4  # roughly sqrt(2) * max_offset
    plt.close("all")


def test_bend_hv_vs_vh_corner_differs():
    stations = lambda: (Diagram()
                        .station("a", 0, 0)
                        .station("b", 3, -2))
    ax_hv = stations().line("l", "#000", [["a", "b"]], bend="hv").render()
    ax_vh = stations().line("l", "#000", [["a", "b"]], bend="vh").render()
    # L-bends render as PathPatch with a Bezier-rounded corner; the corner
    # control point differs between hv (corner at (3, 0)) and vh (corner at (0, -2)).
    def corners(ax):
        return [tuple(p.get_path().vertices.tolist())
                for p in ax.patches if isinstance(p, PathPatch)]
    assert corners(ax_hv) != corners(ax_vh)
    assert len(corners(ax_hv)) == 1 and len(corners(ax_vh)) == 1
    plt.close("all")
