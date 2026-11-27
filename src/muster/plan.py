"""The floor-plan model: rooms, doors and exits on one level, loaded from JSON and validated.

A plan is a dictionary like this (coordinates in millimetres, as numbers or decimal strings):

    {
      "rooms": [{"id": "office", "occupants": 12,
                 "outline": [[0, 0], [6000, 0], [6000, 4000], [0, 4000]]}],
      "doors": [{"id": "d1", "between": ["office", "outside"],
                 "from": [6000, 1000], "to": [6000, 2000]}]
    }

A door is a stretch of wall. It joins two rooms, or a room and "outside" (an exit), and it
must lie along a wall of every room it joins. Its width is the length of that stretch.
Validation never stops at the first problem: it reports every one, each naming the element.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

from muster.geometry import Point, distance, edges, floors_overlap, is_simple, on_segment, point

OUTSIDE = "outside"


class PlanError(ValueError):
    """The plan file cannot be read as a plan at all."""


@dataclass(frozen=True)
class Room:
    id: str
    outline: tuple[Point, ...]
    occupants: int


@dataclass(frozen=True)
class Door:
    id: str
    between: tuple[str, str]
    start: Point
    end: Point

    @property
    def is_exit(self) -> bool:
        return OUTSIDE in self.between

    @property
    def width(self) -> float:
        """The clear width in millimetres: the length of the stretch of wall."""
        return distance(self.start, self.end)


@dataclass(frozen=True)
class Problem:
    """One thing wrong with a plan: the element it is about, and what is wrong."""

    element: str
    message: str

    def __str__(self) -> str:
        return f"{self.element}: {self.message}"


@dataclass(frozen=True)
class Plan:
    rooms: tuple[Room, ...]
    doors: tuple[Door, ...]

    def room(self, room_id: str) -> Room:
        for r in self.rooms:
            if r.id == room_id:
                return r
        raise KeyError(room_id)


def _point(value: Any, where: str) -> Point:
    if not isinstance(value, list) or len(value) != 2:
        raise PlanError(f"{where}: a point must be a list of two numbers, found {value!r}")
    try:
        return point(*(str(v) if isinstance(v, float) else v for v in value))
    except (TypeError, ValueError) as exc:
        raise PlanError(f"{where}: {value!r} is not a point") from exc


def load(data: Any) -> Plan:
    """Read a plan from its JSON form. Raises PlanError if it is not shaped like a plan;
    whether the plan makes sense is for validate()."""
    if not isinstance(data, dict):
        raise PlanError("a plan must be an object with rooms and doors")
    rooms = []
    for i, r in enumerate(data.get("rooms", [])):
        where = f"rooms[{i}]"
        if not isinstance(r, dict) or not isinstance(r.get("id"), str):
            raise PlanError(f"{where}: a room needs a string id")
        occupants = r.get("occupants", 0)
        if not isinstance(occupants, int) or isinstance(occupants, bool):
            raise PlanError(f"room {r['id']}: occupants must be a whole number")
        outline = r.get("outline")
        if not isinstance(outline, list):
            raise PlanError(f"room {r['id']}: outline must be a list of points")
        rooms.append(Room(r["id"], tuple(_point(p, f"room {r['id']}") for p in outline), occupants))
    doors = []
    for i, d in enumerate(data.get("doors", [])):
        where = f"doors[{i}]"
        if not isinstance(d, dict) or not isinstance(d.get("id"), str):
            raise PlanError(f"{where}: a door needs a string id")
        between = d.get("between")
        if not (isinstance(between, list) and len(between) == 2):
            raise PlanError(f"door {d['id']}: between must name two rooms")
        doors.append(
            Door(
                d["id"],
                (str(between[0]), str(between[1])),
                _point(d.get("from"), f"door {d['id']}"),
                _point(d.get("to"), f"door {d['id']}"),
            )
        )
    return Plan(tuple(rooms), tuple(doors))


def _on_a_wall(door: Door, room: Room) -> bool:
    return any(
        on_segment(door.start, a, b) and on_segment(door.end, a, b) for a, b in edges(room.outline)
    )


def validate(plan: Plan) -> list[Problem]:
    """Every problem with the plan, each naming its element. An empty list means valid."""
    problems: list[Problem] = []
    ids = [r.id for r in plan.rooms]
    for room_id in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(Problem(f"room {room_id}", "the id is used by more than one room"))
    if OUTSIDE in ids:
        problems.append(Problem(f"room {OUTSIDE}", f"'{OUTSIDE}' is reserved for exits"))
    door_ids = [d.id for d in plan.doors]
    for door_id in sorted({i for i in door_ids if door_ids.count(i) > 1}):
        problems.append(Problem(f"door {door_id}", "the id is used by more than one door"))

    good = []
    for r in plan.rooms:
        if r.occupants < 0:
            problems.append(Problem(f"room {r.id}", "occupants cannot be negative"))
        if is_simple(r.outline):
            good.append(r)
        else:
            problems.append(
                Problem(f"room {r.id}", "the outline is not a simple polygon with an area")
            )
    for i, r in enumerate(good):
        for s in good[i + 1 :]:
            if floors_overlap(r.outline, s.outline):
                problems.append(Problem(f"room {r.id}", f"overlaps room {s.id}"))

    known = {r.id: r for r in plan.rooms}
    for d in plan.doors:
        if d.start == d.end:
            problems.append(Problem(f"door {d.id}", "has no width"))
        if d.between[0] == d.between[1]:
            problems.append(Problem(f"door {d.id}", "joins a room to itself"))
        for side in d.between:
            if side == OUTSIDE:
                continue
            if side not in known:
                problems.append(Problem(f"door {d.id}", f"names unknown room {side}"))
            elif known[side] in good and not _on_a_wall(d, known[side]):
                problems.append(Problem(f"door {d.id}", f"does not lie on a wall of room {side}"))

    if plan.rooms and not any(d.is_exit for d in plan.doors):
        problems.append(Problem("plan", "has no exit: no door leads outside"))
    else:
        reachable = _reachable_from_outside(plan)
        for r in plan.rooms:
            if r.id not in reachable:
                problems.append(Problem(f"room {r.id}", "no route through doors leads to an exit"))
    return problems


def _reachable_from_outside(plan: Plan) -> set[str]:
    neighbours: dict[str, set[str]] = {}
    for d in plan.doors:
        a, b = d.between
        neighbours.setdefault(a, set()).add(b)
        neighbours.setdefault(b, set()).add(a)
    seen = {OUTSIDE}
    queue = deque([OUTSIDE])
    while queue:
        here = queue.popleft()
        for there in neighbours.get(here, ()):
            if there not in seen:
                seen.add(there)
                queue.append(there)
    return seen
