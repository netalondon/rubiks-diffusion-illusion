# Rubik's Diffusion Illusion

This repo combines a browser-based Rubik's cube viewer, a deterministic tile-remapping pipeline, and Python experiment tooling for diffusion-illusion research.

## Project Layout

- `src/`: browser app, cube model/renderer logic, input handling, and UI wiring
- `scripts/`: TypeScript and Python utilities for exporting specs, searching scrambles, and rendering derived faces
- `python_bridge/`: reusable Python operators for PIL and torch-based face rendering
- `tests/`: TypeScript and Python validation
- `public/generated/`: checked-in generated JSON that the app and scripts consume
- `experiments/`: notebooks and the local face-sweep workflow
- `docs/`: current project status and deeper workflow notes

## Common Commands

```bash
npm install
npm run dev
npm run typecheck
npm test
```

Useful workflow commands:

```bash
npm run find:nonadjacent-scramble
npm run inspect:saved-scramble
npm run export:rubiks-illusion-spec
npm run setup:python-bridge
npm run render:rubiks-illusion-spec
```

## Notes

- `npm test` now runs both the TypeScript and Python test suites.
- The main handoff doc for active project status is [`docs/current-status.md`](./docs/current-status.md).
- The deeper implementation and experiment context lives in [`docs/rubiks-diffusion-illusion-plan.md`](./docs/rubiks-diffusion-illusion-plan.md).
