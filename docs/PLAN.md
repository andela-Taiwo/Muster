# Plan

Muster is built in sessions, each with a clear success test. Later sessions build on earlier
ones, and no layer starts until the one below passes its gates.

## How correctness is proven

- **Independent references.** Each computed quantity is checked against something written
  separately: walking distance against a grid search over the plan, evacuation times against
  the closed-form flow (hydraulic) calculations for corridors, doors and stairs, and the
  agent model against the flow model.
- **An independent checker.** It reads only the plan file, the rule set and the report, and
  re-derives every finding. It never imports the engine.
- **Generated plans.** A seeded generator builds valid plans (offices, corridors, multi-level
  buildings with stairs) and invalid ones, and every check runs over thousands of them. A
  failure is a seed and a shrunk plan that replays.
- **Planted bugs.** Deliberately broken engines that the checks must catch, kept as tests.

Every claim is stated with its bounds: "zero differences on N generated plans of this kind",
never "correct".

## The numbers

- **Distances:** on 10,000 generated plans, every travel distance is within 0.5% of the grid
  reference at its finest resolution, and never shorter than the straight line.
- **Rules:** every rule has a plan that obeys it and a plan that breaks it by the smallest
  step the geometry allows; the checker agrees with the engine on every finding of 10,000
  generated plans.
- **Evacuation:** for single corridors, doors and stairs, flow-model times within 1% of the
  closed-form calculation; agent-model times within 10% of the flow model on generated
  buildings, with the difference explained by kind.
- **Teeth:** at least 12 planted bugs, each caught:
  1. straight-line distance used instead of walking distance;
  2. a wall ignored, so a path walks through it;
  3. door width counted twice for a door between two rooms;
  4. occupant load rounded down instead of up;
  5. a dead end measured from the wrong end;
  6. two exits counted as separate when they share a corridor;
  7. a stair counted as an exit on every level instead of only at ground;
  8. the worst point in a room taken as its centre;
  9. a lost compartment that leaves its own doors usable;
  10. flow through a door not limited by its width;
  11. walking speed not reduced on stairs;
  12. a rule's limit compared with less-than where the rule says at most.
- **Scale:** a 40-storey building with 4,000 rooms checked within a stated time budget, with
  benchmarks that fail the build on regression.

## Sessions

| # | Session | Success |
|---|---|---|
| 1 | Plans: multi-level plan format (levels, rooms, doors, stairs, exits, occupant loads, fire-resisting walls), validation that names the element, and the seeded plan generator | Every generated valid plan validates clean; every generated invalid plan is rejected with the planted problem named; load, save and load again gives the same plan |
| 2 | Walking distance: shortest paths inside rooms around walls and obstacles, through doors and down stairs, to the nearest exit, from the worst point of each room | Within 0.5% of the grid reference on 10,000 generated plans; never shorter than the straight line; bugs 1, 2 and 8 caught |
| 3 | Rules and the checker: the rule set as data (travel distance, exit count and width, dead ends, common paths, exit separation), findings with evidence, and the independent checker | The checker agrees with the engine on every finding of 10,000 generated plans; every rule has its obey and break plans; bugs 3 to 7 and 12 caught |
| 4 | Compartments and resilience: fire compartments from fire-resisting walls, protected stairs, and every plan re-checked with each compartment and each exit lost in turn | Every single loss is checked; the worst one is named per plan; bug 9 caught |
| 5 | Evacuation: a flow model (speed by density, flow limited by door and stair width) and an agent model | Flow model within 1% of the closed forms; agent model within 10% of the flow model on generated buildings; bugs 10 and 11 caught |
| 6 | Reports and the plan view: a compliance report per plan and a drawing of each level with findings, routes and the worst points marked | Every finding in the report appears in the drawing and the checker's output; the drawing is generated from the plan alone |
| 7 | Scale: the 40-storey building, a command line for engineers, profiling and benchmarks | The large building is checked within budget; benchmarks fail the build on regression |

## Out of scope

Certifying real buildings, reading proprietary CAD or BIM formats, smoke and fire spread
modelling, and a web application. The hours go to the references and the checker.
