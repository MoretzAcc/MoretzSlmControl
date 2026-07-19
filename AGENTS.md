# AGENTS.md

This repository is a Python GUI application for controlling SLM displays. It uses PySide6 for the UI, `uv` for dependency management, and Ruff for linting.

## Project shape

- Package root: `src/moretzslmcontrol`
- App entrypoint: `src/moretzslmcontrol/app.py`
- UI layer: `src/moretzslmcontrol/userinterface`
- Monitor/platform integration: `src/moretzslmcontrol/monitor_stuff`
- External SLM control: `src/moretzslmcontrol/external_control`
- Utility helpers: `src/moretzslmcontrol/util`
- API experiments/integration: `src/api`
- Templates/examples: `src/templates`

## Environment

- Python requirement: `>=3.14`
- Dependency manager: `uv`
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

- Format check is not configured separately in this repo. Do not assume auto-formatting is in place.

## Current repo realities

- There is no test suite in the repository yet.
- The application is GUI-first; many changes are best verified by running the app.
- Platform-specific monitor code exists for Linux and Windows under `monitor_stuff/platform`.
- README is still sparse and contains TODOs rather than full usage documentation.

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
2. If UI or runtime behavior changed, run `uv run moretzslmcontrol` when the environment supports GUI execution.
3. If a task affects platform-specific code, call out which platforms were not verified.

## Notes for future work

- Be explicit about GUI/runtime verification limitations in headless environments.
- If adding tests later, place them in a standard `tests/` directory and update this file.
- If README gains authoritative setup or usage instructions, keep this file aligned with it.
