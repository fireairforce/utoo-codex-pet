---
name: utoo-codex-pet
description: Install the bundled Utoo custom Codex desktop pet, a blue-and-white utoopack bunny mascot with generated Codex pet animations. Use when the user wants to install, restore, or share the local Utoo Codex pet.
---

# utoo-codex-pet

This skill installs the bundled Utoo Codex desktop pet, based on the [Utoo](https://github.com/utooland/utoo) visual references, into:

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

## What It Installs

- Pet id: `utoo`
- Display name: `Utoo`
- Assets: `pet.json`, `spritesheet.webp`, `spritesheet.png`, and `source-mapping.json`

The installer verifies bundled files before copying them.
