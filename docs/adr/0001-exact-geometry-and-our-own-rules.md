# 0001: Exact geometry, and a rule set of our own

## Status

Accepted

## Context

A compliance finding is only useful if it is right at the boundary: a door either lies on a
wall or it does not, two rooms either overlap or they share a wall. Floating-point geometry
gets these cases wrong in ways that depend on the order of operations, and a plan that passes
on one machine can fail on another.

Building codes state their rules in copyrighted documents, vary by country, and change. A
project that copies them inherits those problems and implies a certification it cannot give.

## Decision

- Plan coordinates are exact rationals (`fractions.Fraction`, millimetres). Every predicate
  (orientation, intersection, containment, overlap) is computed exactly. Floating point is
  used only for reported distances and times, never for a yes-or-no decision.
- The rule set is our own, written as data in the repository, with the reason for every
  number. It covers the kinds of rules fire engineers use (travel distance, exit count and
  width, dead ends, exit separation, compartments), not any code's text.
- Muster never claims a real building complies with a real code.

## Consequences

- Boundary cases are decided the same way everywhere, and can be tested exactly.
- Exact arithmetic is slower; large plans in session 7 must show it stays within budget.
- Anyone using Muster for a real building must map their own code's rules onto the rule
  format; the format is designed to make that possible.
