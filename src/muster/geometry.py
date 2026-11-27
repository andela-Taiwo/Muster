"""Exact plane geometry for floor plans.

Coordinates are exact rationals in millimetres, so every yes-or-no question (is this point on
that wall, do these two rooms overlap) has one answer on every machine. Floating point is only
used for distances that are reported, never for decisions. See ADR 0001.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence
from enum import Enum
from fractions import Fraction

Point = tuple[Fraction, Fraction]
Polygon = Sequence[Point]


def point(x: int | str | Fraction, y: int | str | Fraction) -> Point:
    """A point from exact values: integers, fractions, or decimal strings such as "1.25"."""
    return (Fraction(x), Fraction(y))


def cross(o: Point, a: Point, b: Point) -> Fraction:
    """Twice the signed area of triangle o, a, b: positive if a to b turns left around o."""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def signed_area2(poly: Polygon) -> Fraction:
    """Twice the signed area of a polygon: positive when its vertices run anticlockwise."""
    total = Fraction(0)
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        total += p[0] * q[1] - q[0] * p[1]
    return total


def area(poly: Polygon) -> Fraction:
    """The polygon's area, whichever way its vertices run."""
    return abs(signed_area2(poly)) / 2


def edges(poly: Polygon) -> list[tuple[Point, Point]]:
    """The polygon's edges, each from a vertex to the next, closing back to the first."""
    return [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]


def on_segment(p: Point, a: Point, b: Point) -> bool:
    """Whether p lies on the closed segment from a to b."""
    if cross(a, b, p) != 0:
        return False
    return min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])


def segments_touch(a: Point, b: Point, c: Point, d: Point) -> bool:
    """Whether the closed segments ab and cd share at least one point."""
    d1, d2 = cross(c, d, a), cross(c, d, b)
    d3, d4 = cross(a, b, c), cross(a, b, d)
    if ((d1 > 0 > d2) or (d1 < 0 < d2)) and ((d3 > 0 > d4) or (d3 < 0 < d4)):
        return True
    return on_segment(a, c, d) or on_segment(b, c, d) or on_segment(c, a, b) or on_segment(d, a, b)


def proper_crossing(a: Point, b: Point, c: Point, d: Point) -> Point | None:
    """The point where ab and cd cross in both of their interiors, or None."""
    d1, d2 = cross(c, d, a), cross(c, d, b)
    d3, d4 = cross(a, b, c), cross(a, b, d)
    if ((d1 > 0 > d2) or (d1 < 0 < d2)) and ((d3 > 0 > d4) or (d3 < 0 < d4)):
        t = d1 / (d1 - d2)
        return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
    return None


def is_simple(poly: Polygon) -> bool:
    """Whether the polygon has at least three vertices, a non-zero area, and no edge that
    touches another except where neighbouring edges meet."""
    n = len(poly)
    if n < 3 or len(set(poly)) != n or signed_area2(poly) == 0:
        return False
    sides = edges(poly)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = sides[i]
            c, d = sides[j]
            if j == i + 1 or (i == 0 and j == n - 1):
                # Neighbours share one vertex; they must not overlap along a line.
                shared = b if j == i + 1 else a
                other_i = a if j == i + 1 else b
                other_j = d if j == i + 1 else c
                if cross(shared, other_i, other_j) == 0 and (
                    on_segment(other_j, shared, other_i) or on_segment(other_i, shared, other_j)
                ):
                    return False
                continue
            if segments_touch(a, b, c, d):
                return False
    return True


class Where(Enum):
    """Where a point lies relative to a polygon."""

    INSIDE = "inside"
    BOUNDARY = "boundary"
    OUTSIDE = "outside"


def locate(poly: Polygon, p: Point) -> Where:
    """Whether p is inside the polygon, on its boundary, or outside it (crossing rule)."""
    for a, b in edges(poly):
        if on_segment(p, a, b):
            return Where.BOUNDARY
    inside = False
    for a, b in edges(poly):
        if (a[1] > p[1]) != (b[1] > p[1]):
            x = a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x > p[0]:
                inside = not inside
    return Where.INSIDE if inside else Where.OUTSIDE


def _pieces(a: Point, b: Point, other: Polygon) -> list[tuple[Point, Point]]:
    """Segment ab cut at every point where the other polygon's boundary meets it, so that each
    piece lies wholly inside, wholly outside, or wholly on the other polygon's boundary."""
    cuts = {a, b}
    for c, d in edges(other):
        crossing = proper_crossing(a, b, c, d)
        if crossing is not None:
            cuts.add(crossing)
        for v in (c, d):
            if on_segment(v, a, b):
                cuts.add(v)
    direction = (b[0] - a[0], b[1] - a[1])
    ordered = sorted(
        cuts, key=lambda q: (q[0] - a[0]) * direction[0] + (q[1] - a[1]) * direction[1]
    )
    return list(itertools.pairwise(ordered))


def _boundary_enters(first: Polygon, second: Polygon) -> tuple[bool, bool]:
    """Whether some piece of first's boundary lies strictly inside second, and whether every
    piece lies on second's boundary."""
    enters, all_on_boundary = False, True
    for a, b in edges(first):
        for p, q in _pieces(a, b, second):
            mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            where = locate(second, mid)
            if where is Where.INSIDE:
                enters = True
            if where is not Where.BOUNDARY:
                all_on_boundary = False
    return enters, all_on_boundary


def floors_overlap(first: Polygon, second: Polygon) -> bool:
    """Whether two simple polygons share some area, as opposed to only touching along walls
    or at corners.

    Two simple polygons share area exactly when part of one's boundary runs strictly inside
    the other, or when their boundaries coincide. Each boundary is cut wherever the other
    boundary meets it, so every piece is wholly inside, outside or on the boundary, and its
    midpoint decides which.
    """
    enters_ab, same_ab = _boundary_enters(first, second)
    if enters_ab:
        return True
    enters_ba, same_ba = _boundary_enters(second, first)
    return enters_ba or (same_ab and same_ba)


def distance(p: Point, q: Point) -> float:
    """The straight-line distance between two points, for reporting only."""
    return math.hypot(float(q[0] - p[0]), float(q[1] - p[1]))
