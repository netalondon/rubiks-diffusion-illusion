# Rubik's Diffusion Illusion

This project is based on [Diffusion Illusions](https://diffusionillusions.com/) and adapts that workflow to a Rubik's cube setting.

The goal is to build a Rubik's cube image illusion where the solved cube shows one set of images and the scrambled cube shows another.

## What's here

- `src/`: Vite + Three.js cube viewer and interaction logic
- `python_bridge/`: PIL and torch renderers used by the optimization workflow
- `scripts/`: export, scramble-search, and rendering helpers
- `experiments/`: notebooks and local experiment runs
- `docs/`: project status and implementation notes

## Quick start

```bash
npm install
npm run dev
```

For checks:

```bash
npm run typecheck
npm test
```

## Useful commands

```bash
npm run find:nonadjacent-scramble
npm run export:rubiks-illusion-spec
npm run setup:python-bridge
npm run render:rubiks-illusion-spec
```

## Read next

- [Official Diffusion Illusions site](https://diffusionillusions.com/)
- [`docs/current-status.md`](./docs/current-status.md) for the latest handoff
- [`docs/diffusion-illusion-technique.md`](./docs/diffusion-illusion-technique.md) for the optimization approach
- [`docs/rubiks-diffusion-illusion-plan.md`](./docs/rubiks-diffusion-illusion-plan.md) for deeper project context
