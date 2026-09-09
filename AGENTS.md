# AGENTS.md

This repository is a Python GUI application for controlling SLM displays. It uses PySide6 for the UI, `uv` for dependency management, and Ruff for linting.

## Project shape

- Server package root: `src/moretzslmcontrol`
- Client package root: `client/src/moretzslmclient`
- App entrypoint: `src/moretzslmcontrol/app.py`
- UI layer: `src/moretzslmcontrol/userinterface`
- Monitor/platform integration: `src/moretzslmcontrol/monitor_stuff`
- External SLM control: `src/moretzslmcontrol/control`
- Utility helpers: `src/moretzslmcontrol/util`
- Templates/examples: `src/templates`

## Environment

- Python requirement: `>=3.14`
- Dependency manager: `uv`
- Client Python requirement: `>=3.11`
- Main app run command:

```bash
uv run moretzslmcontrol
```

## Development commands

- Run app:

```bash
uv run moretzslmcontrol
```

- Run Ruff:

```bash
uv run ruff check .
```

- Check the standalone client package:

```bash
uv run ruff check client/src
```

- Format check is not configured separately in this repo. Do not assume auto-formatting is in place.

## Current repo realities

- API contract checks live in `tests/` and use the standard-library `unittest` runner.
- The application is GUI-first; many changes are best verified by running the app.
- Platform-specific monitor code exists for Linux and Windows under `monitor_stuff/platform`.
- The client package must remain independent of GUI, monitor, and SLM-server modules; it may depend only on its own code, HEROS, and NumPy.

## Coding expectations for agents

- Keep changes scoped and consistent with the existing package layout.
- Prefer small, explicit Python changes over broad refactors.
- Preserve platform branching in `app.py` and monitor adapters unless the task explicitly changes platform behavior.
- Treat UI and monitor/session logic as separate concerns; avoid moving hardware logic into widgets.
- Follow existing Ruff constraints from `pyproject.toml`, including type-annotation expectations.
- Do not introduce new tooling, formatters, or test frameworks unless the task requires it.

## Verification expectations

For code changes, use the lightest verification that matches the risk:

1. `uv run ruff check .`
2. `uv run python -m unittest discover -s tests` when changing the server/client HERO contract.
3. If UI or runtime behavior changed, run `uv run moretzslmcontrol` when the environment supports GUI execution.
4. If a task affects platform-specific code, call out which platforms were not verified.

## Notes for future work

- Be explicit about GUI/runtime verification limitations in headless environments.
- If adding tests later, place them in a standard `tests/` directory and update this file.
- If README gains authoritative setup or usage instructions, keep this file aligned with it.
