# utoo-codex-pet

Utoo is a custom Codex desktop pet generated from the [Utoo](https://github.com/utooland/utoo) / utoopack visual references. It is a compact blue-and-white bunny-like mascot with pixel-adjacent Codex pet styling.

Utoo 是一个基于 [Utoo](https://github.com/utooland/utoo) / utoopack 视觉参考生成的 Codex 桌面宠物。它保留了蓝白兔形轮廓，并整理成可本地安装、分享和复用的目录仓库。

## Watchdog Features

The repo also includes a local Codex skill and watchdog script so Utoo can help watch utoopack-related work:

- Watch `smallfish`, `bigfish`, `father`, and `dumi` projects for utoopack build setup and likely failure points.
- Wrap utoopack build or dependency installation commands, capture logs, classify failures, and generate reports for Codex AI analysis.
- Inspect local Codex skill and pet installation state.

这个仓库现在不只是宠物资源，也包含一个本地 Codex skill / watchdog 脚本：

- 盯防 `smallfish` / `bigfish` / `father` / `dumi` 项目的 utoopack 构建任务。
- 盯防 utoopack 依赖安装问题，并为失败任务保留日志和故障分类。
- 检查本地 Codex skills / pets 环境。

## Preview

| State | Preview | Frames |
| --- | --- | --- |
| Idle | <img src="assets/previews/idle.png" width="96" alt="Idle preview"> | 6 |
| Running Right | <img src="assets/previews/running-right.png" width="96" alt="Running right preview"> | 8 |
| Running Left | <img src="assets/previews/running-left.png" width="96" alt="Running left preview"> | 8 |
| Waving | <img src="assets/previews/waving.png" width="96" alt="Waving preview"> | 4 |
| Jumping | <img src="assets/previews/jumping.png" width="96" alt="Jumping preview"> | 5 |
| Failed | <img src="assets/previews/failed.png" width="96" alt="Failed preview"> | 8 |
| Waiting | <img src="assets/previews/waiting.png" width="96" alt="Waiting preview"> | 6 |
| Running | <img src="assets/previews/running.png" width="96" alt="Running preview"> | 6 |
| Review | <img src="assets/previews/review.png" width="96" alt="Review preview"> | 6 |

Full QA contact sheet:

<img src="assets/qa/contact-sheet.png" width="480" alt="Utoo QA contact sheet">

## Install

From this repository:

```bash
bash scripts/install_utoo.sh
```

The pet will be installed to:

```bash
${CODEX_HOME:-$HOME/.codex}/pets/utoo
```

Then restart Codex or refresh the pet list and select `Utoo`.

Install the watchdog skill:

```bash
bash scripts/install_skill.sh
```

Use the watchdog directly:

```bash
python3 scripts/utoo_watchdog.py scan --project /path/to/project
python3 scripts/utoo_watchdog.py run --project /path/to/project --label utoopack-build -- pnpm build
python3 scripts/utoo_watchdog.py run --project /path/to/project --label deps-install -- pnpm install
python3 scripts/utoo_watchdog.py codex
```

Reports are written to `reports/` by default. In Codex, you can ask: `用 $utoo-codex-pet 盯防这个项目的 utoopack 构建任务`.

## Included

- `SKILL.md`: Codex skill instructions for installing this pet and running the Utoo watchdog.
- `scripts/install_utoo.sh`: local installer.
- `scripts/install_skill.sh`: installs this repo as a local Codex skill.
- `scripts/utoo_watchdog.py`: project / command / Codex skill watchdog.
- `assets/utoo/pet.json`: pet metadata.
- `assets/utoo/spritesheet.webp`: Codex-ready animation atlas.
- `assets/utoo/spritesheet.png`: PNG copy of the atlas for inspection.
- `assets/utoo/source-mapping.json`: generation and row mapping metadata.
- `assets/previews/*.png`: first-frame previews for README browsing.
- `assets/qa/contact-sheet.png`: full row-by-row QA sheet.
- `assets/qa/videos/*.mp4`: per-state animation previews.
- `assets/references/*.png`: source and canonical reference images used for generation.

## Validation

The final atlas was validated with the `hatch-pet` QA pipeline:

- Atlas: 1536 x 1872, RGBA WebP.
- Cell size: 192 x 208.
- Rows: 9.
- Validation errors: 0.
- Validation warnings: 0.

## Notes

`running-left` was derived by deterministic mirroring from `running-right`; the source mascot has no readable text, side-specific marking, or handed prop, so mirroring preserves the pet identity and direction semantics.
