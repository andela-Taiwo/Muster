# Muster

Fire-safety egress checking and evacuation simulation for building plans. Muster reads a
floor plan (rooms, doors, stairs, exits and how many people each room holds) and answers
the questions a fire engineer asks: how far is the walk to an exit, are there enough exits
and are they wide enough, is any corridor a dead end, can everyone still get out if one fire
compartment is lost, and how long does it take.

> **Status: foundation only.** The project layout, tooling, exact plane geometry and the
> floor-plan model with its validation exist and are tested. Travel distances, the rules,
> compartments, evacuation and reports are not built yet. See [the plan](docs/PLAN.md).

## What it will do

- **Read** multi-level plans as JSON: rooms as polygons, doors with widths, stairs, exits,
  occupant loads, fire-resisting walls.
- **Measure** the real walking distance from every point of every room to the nearest exit,
  around walls and through doors, not straight-line guesses.
- **Check** a stated rule set: travel distance, number and width of exits, dead ends, common
  paths, exit separation. Every finding names the room, door or route and the numbers.
- **Stress** the plan: lose any one compartment or exit and check everyone can still leave.
- **Simulate** evacuation with a flow model and an agent model, checked against each other.
- **Report** every finding with its evidence, and draw the plan with the findings marked.

## How it is proven

- **Independent references.** Walking distances are checked against an independent grid
  search; evacuation times against the closed-form flow calculations for corridors, doors and
  stairs; the agent model against the flow model.
- **An independent checker** re-derives every finding from the plan file alone and never
  imports the code that produced it.
- **Planted bugs.** Deliberately broken engines the checks must catch, kept as tests.
- **Our own rule set.** The rules are written here, as data, with a source for every number.
  No building code's text is copied, and Muster does not certify any real building.

## What exists today

| Module | What it does |
|---|---|
| `muster.geometry` | Exact plane geometry with rational coordinates: signed area, simple polygons, segment intersection, point in polygon, and whether two rooms' floors overlap |
| `muster.plan` | The floor-plan model loaded from JSON, with validation that names the element and the problem: broken rooms, overlapping rooms, doors not on a shared wall, unknown rooms, no exit, rooms that cannot reach an exit |

## Quickstart

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12.

```bash
make setup   # install locked dependencies
make check   # lint, format check, type check and tests
make help    # list every target
```

## Layout

```
src/muster/   # the engine
tests/        # unit and property tests
docs/PLAN.md  # what is being built, in order, and the numbers it is held to
docs/adr/     # architecture decision records
```

## Licence

MIT. See [LICENSE](LICENSE).
