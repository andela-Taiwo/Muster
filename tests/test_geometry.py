"""Exact geometry: hand-checked cases, and properties over generated shapes."""

from fractions import Fraction

from hypothesis import given, settings
from hypothesis import strategies as st

from muster.geometry import (
    Point,
    Where,
    area,
    floors_overlap,
    is_simple,
    locate,
    on_segment,
    point,
    proper_crossing,
    segments_touch,
    signed_area2,
)

SETTINGS = settings(max_examples=300, deadline=None, derandomize=True)


def rect(x0: int, y0: int, x1: int, y1: int) -> list[Point]:
    return [point(x0, y0), point(x1, y0), point(x1, y1), point(x0, y1)]


def test_points_take_exact_decimal_strings() -> None:
    assert point("1.25", "-0.5") == (Fraction(5, 4), Fraction(-1, 2))


def test_the_area_of_a_rectangle_and_its_direction() -> None:
    square = rect(0, 0, 4, 3)
    assert area(square) == 12
    assert signed_area2(square) == 24
    assert signed_area2(list(reversed(square))) == -24


def test_the_area_of_an_l_shaped_room() -> None:
    room = [point(0, 0), point(6, 0), point(6, 2), point(2, 2), point(2, 5), point(0, 5)]
    assert area(room) == 6 * 2 + 2 * 3


def test_on_segment_includes_the_ends_and_excludes_the_line_beyond() -> None:
    a, b = point(0, 0), point(4, 4)
    assert on_segment(point(0, 0), a, b)
    assert on_segment(point(1, 1), a, b)
    assert not on_segment(point(5, 5), a, b)
    assert not on_segment(point(1, 2), a, b)


def test_segments_that_cross_touch_or_miss() -> None:
    assert segments_touch(point(0, 0), point(4, 4), point(0, 4), point(4, 0))
    assert segments_touch(point(0, 0), point(2, 0), point(2, 0), point(2, 3))
    assert segments_touch(point(0, 0), point(4, 0), point(2, 0), point(6, 0))
    assert not segments_touch(point(0, 0), point(1, 0), point(2, 0), point(3, 0))
    assert not segments_touch(point(0, 0), point(4, 0), point(0, 1), point(4, 1))


def test_a_proper_crossing_is_found_exactly() -> None:
    crossing = proper_crossing(point(0, 0), point(3, 3), point(0, 1), point(3, 1))
    assert crossing == (Fraction(1), Fraction(1))
    assert proper_crossing(point(0, 0), point(2, 0), point(2, 0), point(2, 3)) is None


def test_simple_and_not_simple_polygons() -> None:
    assert is_simple(rect(0, 0, 2, 2))
    bow_tie = [point(0, 0), point(2, 2), point(2, 0), point(0, 2)]
    assert not is_simple(bow_tie)
    assert not is_simple([point(0, 0), point(1, 1), point(2, 2)])
    assert not is_simple([point(0, 0), point(2, 0)])
    doubled_back = [point(0, 0), point(4, 0), point(2, 0), point(2, 2)]
    assert not is_simple(doubled_back)


def test_locating_points() -> None:
    square = rect(0, 0, 4, 4)
    assert locate(square, point(2, 2)) is Where.INSIDE
    assert locate(square, point(4, 2)) is Where.BOUNDARY
    assert locate(square, point(0, 0)) is Where.BOUNDARY
    assert locate(square, point(5, 2)) is Where.OUTSIDE


def test_rooms_that_share_a_wall_do_not_overlap() -> None:
    assert not floors_overlap(rect(0, 0, 2, 2), rect(2, 0, 4, 2))
    assert not floors_overlap(rect(0, 0, 2, 2), rect(2, 2, 4, 4))
    assert not floors_overlap(rect(0, 0, 2, 2), rect(2, 1, 4, 5))


def test_rooms_that_share_floor_overlap() -> None:
    assert floors_overlap(rect(0, 0, 2, 2), rect(1, 0, 3, 2))  # no edges cross properly
    assert floors_overlap(rect(0, 0, 4, 4), rect(1, 1, 2, 2))  # one inside the other
    assert floors_overlap(rect(0, 0, 2, 2), rect(0, 0, 2, 2))  # the same room twice
    assert floors_overlap(rect(0, 0, 2, 2), rect(1, 1, 3, 3))


coordinate = st.integers(min_value=-20, max_value=20)


@st.composite
def rectangles(draw: st.DrawFn) -> tuple[int, int, int, int]:
    x0, x1 = sorted(draw(st.lists(coordinate, min_size=2, max_size=2, unique=True)))
    y0, y1 = sorted(draw(st.lists(coordinate, min_size=2, max_size=2, unique=True)))
    return x0, y0, x1, y1


@SETTINGS
@given(rectangles(), rectangles())
def test_rectangle_overlap_matches_the_interval_rule(
    r: tuple[int, int, int, int], s: tuple[int, int, int, int]
) -> None:
    expected = min(r[2], s[2]) > max(r[0], s[0]) and min(r[3], s[3]) > max(r[1], s[1])
    assert floors_overlap(rect(*r), rect(*s)) == expected
    assert floors_overlap(rect(*s), rect(*r)) == expected


@SETTINGS
@given(rectangles(), coordinate, coordinate)
def test_area_does_not_change_when_a_room_moves(
    r: tuple[int, int, int, int], dx: int, dy: int
) -> None:
    moved = [(x + dx, y + dy) for x, y in rect(*r)]
    assert area(moved) == area(rect(*r)) == (r[2] - r[0]) * (r[3] - r[1])
    assert is_simple(moved)
