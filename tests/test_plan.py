"""The plan model: a small office floor that is valid, and each kind of mistake named."""

import copy
import json
from typing import Any

import pytest

from muster.plan import OUTSIDE, PlanError, load, validate

# An office and a corridor along its south wall; the corridor has the only exit, at its east
# end. Millimetres.
OFFICE: dict[str, Any] = {
    "rooms": [
        {
            "id": "office",
            "occupants": 12,
            "outline": [[0, 2000], [8000, 2000], [8000, 6000], [0, 6000]],
        },
        {
            "id": "corridor",
            "occupants": 0,
            "outline": [[0, 0], [8000, 0], [8000, 2000], [0, 2000]],
        },
    ],
    "doors": [
        {"id": "d1", "between": ["office", "corridor"], "from": [3000, 2000], "to": [3900, 2000]},
        {"id": "exit", "between": ["corridor", OUTSIDE], "from": [8000, 500], "to": [8000, 1500]},
    ],
}


def problems_of(data: dict[str, Any]) -> list[str]:
    return [str(p) for p in validate(load(data))]


def changed(**changes: Any) -> dict[str, Any]:
    data = copy.deepcopy(OFFICE)
    for path, value in changes.items():
        kind, index, key = path.split("__")
        data[kind][int(index)][key] = value
    return data


def test_the_office_floor_is_valid() -> None:
    assert problems_of(OFFICE) == []


def test_a_plan_survives_a_round_trip_through_json() -> None:
    assert load(json.loads(json.dumps(OFFICE))) == load(OFFICE)


def test_decimal_coordinates_are_exact() -> None:
    data = changed(doors__0__to=["3900.5", 2000])
    plan = load(data)
    assert plan.doors[0].width == pytest.approx(900.5)
    assert problems_of(data) == []


def test_a_door_knows_its_width_and_whether_it_is_an_exit() -> None:
    plan = load(OFFICE)
    assert plan.doors[0].width == pytest.approx(900)
    assert not plan.doors[0].is_exit
    assert plan.doors[1].is_exit


def test_a_room_whose_outline_crosses_itself() -> None:
    bow_tie = [[0, 2000], [8000, 6000], [8000, 2000], [0, 6000]]
    assert "room office: the outline is not a simple polygon with an area" in problems_of(
        changed(rooms__0__outline=bow_tie)
    )


def test_rooms_that_overlap() -> None:
    lower = [[0, 1000], [8000, 1000], [8000, 6000], [0, 6000]]
    assert "room office: overlaps room corridor" in problems_of(changed(rooms__0__outline=lower))


def test_a_door_that_is_not_on_a_shared_wall() -> None:
    assert "door d1: does not lie on a wall of room corridor" in problems_of(
        changed(doors__0__from=[3000, 2500], doors__0__to=[3900, 2500])
    )


def test_a_door_to_an_unknown_room() -> None:
    assert "door d1: names unknown room kitchen" in problems_of(
        changed(doors__0__between=["office", "kitchen"])
    )


def test_a_door_with_no_width() -> None:
    assert "door d1: has no width" in problems_of(changed(doors__0__to=[3000, 2000]))


def test_a_plan_with_no_exit() -> None:
    data = copy.deepcopy(OFFICE)
    data["doors"] = data["doors"][:1]
    assert problems_of(data) == ["plan: has no exit: no door leads outside"]


def test_a_room_that_cannot_reach_an_exit() -> None:
    data = copy.deepcopy(OFFICE)
    data["doors"] = data["doors"][1:]
    assert problems_of(data) == ["room office: no route through doors leads to an exit"]


def test_every_problem_is_reported_not_just_the_first() -> None:
    data = changed(rooms__0__occupants=-3, doors__0__to=[3000, 2000])
    found = problems_of(data)
    assert "room office: occupants cannot be negative" in found
    assert "door d1: has no width" in found


def test_duplicate_ids_and_the_reserved_name() -> None:
    data = copy.deepcopy(OFFICE)
    data["rooms"][1]["id"] = "office"
    assert "room office: the id is used by more than one room" in problems_of(data)
    data = changed(rooms__1__id=OUTSIDE)
    assert f"room {OUTSIDE}: '{OUTSIDE}' is reserved for exits" in problems_of(data)


@pytest.mark.parametrize(
    "data",
    [
        [],
        {"rooms": [{"outline": []}]},
        {"rooms": [{"id": "a", "occupants": 1.5, "outline": []}]},
        {"rooms": [{"id": "a", "outline": [[0, 0, 0]]}]},
        {"doors": [{"id": "d", "between": ["a"], "from": [0, 0], "to": [1, 0]}]},
    ],
)
def test_input_that_is_not_shaped_like_a_plan_is_refused(data: Any) -> None:
    with pytest.raises(PlanError):
        load(data)
