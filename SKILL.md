---
name: utoo-codex-pet
description: Use when the user wants Utoo, the custom Codex pet, to watch or analyze utoopack build tasks in smallfish, bigfish, father, or dumi projects; diagnose utoopack dependency installation failures; inspect Codex skill/pet runtime state; or install/restore/share the bundled Utoo Codex pet.
---

# utoo-codex-pet

Utoo is a Codex pet with a bundled watchdog workflow. The pet provides the visual identity; the scripts provide deterministic monitoring and report generation.

The bundled Utoo Codex desktop pet, based on the [Utoo](https://github.com/utooland/utoo) visual references, installs into:

```bash
${CODEX_HOME:-$HOME/.codex}/pets/utoo
```

## Install

If this skill is installed under Codex skills, run:

```bash
bash "${CODEX_HOME:-$HOME/.codex}/skills/utoo-codex-pet/scripts/install_utoo.sh"
```

If you are inside this repository, run:

```bash
bash scripts/install_utoo.sh
```

After installation, restart Codex or refresh the pet list, then select `Utoo`.

To install this watchdog as a local Codex skill, run:

```bash
bash scripts/install_skill.sh
```

## Watchdog Workflow

Choose the action based on the request:

- Check a `smallfish`, `bigfish`, `father`, or `dumi` project before a build:
  ```bash
  python3 scripts/utoo_watchdog.py scan --project <project>
  ```
- Watch a build, install, or other task:
  ```bash
  python3 scripts/utoo_watchdog.py run --project <project> --label <name> -- <command...>
  ```
- Check local Codex skills and pet installation:
  ```bash
  python3 scripts/utoo_watchdog.py codex
  ```

After running the watchdog command, read the generated Markdown report in `reports/` and add AI analysis: likely root cause, evidence, confidence, missing information, and concrete next steps. If the user asks for a fix, edit the target project and rerun the failing command.

## What It Installs

- Pet id: `utoo`
- Display name: `Utoo`
- Assets: `pet.json`, `spritesheet.webp`, `spritesheet.png`, and `source-mapping.json`

The installer verifies bundled files before copying them.

## Report Contents

Watchdog reports include:

- project family hints: `smallfish`, `bigfish`, `father`, `dumi`, or generic
- utoopack-related dependency and config signals
- package manager and lockfile signals
- local `SKILL.md` frontmatter checks
- command exit code, captured log path, and failure classification when wrapping a task
- an AI handoff prompt for Codex analysis
