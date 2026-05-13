#!/usr/bin/env python3
"""Utoo watchdog for utoopack builds, dependency installs, and Codex skills."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from typing import Any


UTOOPACK_KEYWORDS = [
    "utoo",
    "utoopack",
    "@umijs/bundler-utoopack",
    "bundler-utoopack",
    "turbopack",
]

PROJECT_FAMILIES = ["smallfish", "bigfish", "father", "dumi"]

FAILURE_PATTERNS = [
    ("missing-module", re.compile(r"(Cannot find module|Module not found|ModuleNotFoundError|ERR_MODULE_NOT_FOUND|Can't resolve)", re.I)),
    ("package-manager", re.compile(r"(ERESOLVE|ELOCKVERIFY|integrity checksum failed|No matching version found|ENOTEMPTY|EEXIST)", re.I)),
    ("network", re.compile(r"(\bETIMEDOUT\b|\bECONNRESET\b|\bECONNREFUSED\b|\bENOTFOUND\b|socket hang up|network timeout)", re.I)),
    ("permission", re.compile(r"(EACCES|EPERM|permission denied|operation not permitted)", re.I)),
    ("node-version", re.compile(r"(Unsupported engine|The engine \"node\" is incompatible|requires Node|node version)", re.I)),
    ("typescript", re.compile(r"(TS\d{4}|TypeScript|tsc .*error)", re.I)),
    ("syntax", re.compile(r"(SyntaxError|Unexpected token|Unexpected identifier)", re.I)),
    ("utoo-build", re.compile(r"(utoopack|bundler-utoopack|turbopack|max dev|max build)", re.I)),
    ("port", re.compile(r"(EADDRINUSE|address already in use|port \d+ is already in use)", re.I)),
]


def now_slug() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-")
    return slug or "utoo-watchdog"


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_text_safe(path: Path, limit: int = 250_000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if len(text) > limit:
        return text[:limit] + "\n...[truncated]...\n"
    return text


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def detect_package_manager(project: Path) -> dict[str, Any]:
    lockfiles = {
        "pnpm": project / "pnpm-lock.yaml",
        "yarn": project / "yarn.lock",
        "npm": project / "package-lock.json",
        "bun": project / "bun.lockb",
    }
    found = [name for name, path in lockfiles.items() if path.exists()]
    return {
        "manager": found[0] if found else "unknown",
        "lockfiles": found,
        "node_modules": (project / "node_modules").exists(),
    }


def package_signals(project: Path) -> dict[str, Any]:
    package_path = project / "package.json"
    package = read_json(package_path) or {}
    deps: dict[str, str] = {}
    for field in ["dependencies", "devDependencies", "peerDependencies", "optionalDependencies"]:
        value = package.get(field)
        if isinstance(value, dict):
            deps.update({k: str(v) for k, v in value.items()})

    scripts = package.get("scripts") if isinstance(package.get("scripts"), dict) else {}
    utoo_deps = {k: v for k, v in deps.items() if any(key in k.lower() for key in UTOOPACK_KEYWORDS)}
    interesting_scripts = {
        k: v for k, v in scripts.items()
        if any(key in f"{k} {v}".lower() for key in UTOOPACK_KEYWORDS + PROJECT_FAMILIES + ["max", "build"])
    }

    return {
        "exists": package_path.exists(),
        "name": package.get("name"),
        "private": package.get("private"),
        "engines": package.get("engines") if isinstance(package.get("engines"), dict) else {},
        "utoo_dependencies": utoo_deps,
        "interesting_scripts": interesting_scripts,
        "script_count": len(scripts),
        "dependency_count": len(deps),
    }


def config_signals(project: Path) -> list[dict[str, Any]]:
    candidates = [
        "config/config.ts",
        "config/config.js",
        ".umirc.ts",
        ".umirc.js",
        "max.config.ts",
        "max.config.js",
        "father.config.ts",
        "father.config.js",
        ".fatherrc.ts",
        ".fatherrc.js",
        ".dumirc.ts",
        ".dumirc.js",
        "tsconfig.json",
        ".npmrc",
    ]
    signals: list[dict[str, Any]] = []
    for name in candidates:
        path = project / name
        if not path.exists():
            continue
        text = read_text_safe(path, limit=80_000)
        matches = [key for key in UTOOPACK_KEYWORDS + PROJECT_FAMILIES if key in text.lower()]
        signals.append({"path": name, "matches": sorted(set(matches)), "size": path.stat().st_size})
    return signals


def detect_family(project: Path, package: dict[str, Any], configs: list[dict[str, Any]]) -> dict[str, Any]:
    haystack_parts = [
        project.name.lower(),
        str(package.get("name") or "").lower(),
        json.dumps(package.get("interesting_scripts", {}), ensure_ascii=False).lower(),
        json.dumps(configs, ensure_ascii=False).lower(),
    ]
    haystack = " ".join(haystack_parts)
    families = [name for name in PROJECT_FAMILIES if name in haystack]
    return {"families": sorted(set(families)) or ["generic"], "evidence": haystack[:1000]}


def scan_skill_files(project: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    ignored = {"node_modules", ".git", "dist", "build", ".next", ".umi"}
    for path in project.rglob("SKILL.md"):
        if any(part in ignored for part in path.parts):
            continue
        text = read_text_safe(path, limit=50_000)
        description = re.search(r"^description:\s*(.+)$", text, re.M)
        description_text = description.group(1).strip() if description else ""
        issues = []
        if not text.startswith("---"):
            issues.append("missing YAML frontmatter")
        if not re.search(r"^name:\s*\S+", text, re.M):
            issues.append("missing name")
        if not description_text:
            issues.append("missing description")
        elif len(description_text) < 40:
            issues.append("description may be too short for reliable triggering")
        results.append({
            "path": rel(path, project),
            "ok": not issues,
            "issues": issues,
            "description_length": len(description_text),
        })
    return results


def recommend_from_scan(package: dict[str, Any], configs: list[dict[str, Any]]) -> list[str]:
    recommendations: list[str] = []
    if not package["exists"]:
        recommendations.append("No package.json found; run from a JS project root or pass --project.")
    if not package["interesting_scripts"]:
        recommendations.append("No obvious utoopack/build script found; identify the exact build command before monitoring.")
    if not package["utoo_dependencies"] and not any(c["matches"] for c in configs):
        recommendations.append("No direct utoopack dependency/config signal found; this may be indirect through the framework.")
    if package["engines"]:
        recommendations.append(f"Check local Node version against package engines: {package['engines']}.")
    return recommendations


def scan_project(project: Path) -> dict[str, Any]:
    project = project.resolve()
    package = package_signals(project)
    configs = config_signals(project)
    return {
        "kind": "project-scan",
        "project": str(project),
        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        "package_manager": detect_package_manager(project),
        "package": package,
        "family": detect_family(project, package, configs),
        "configs": configs,
        "skills": scan_skill_files(project),
        "recommendations": recommend_from_scan(package, configs),
    }


def classify_log(text: str) -> list[dict[str, Any]]:
    findings = []
    lines = text.splitlines()
    for label, pattern in FAILURE_PATTERNS:
        matched = []
        for line in lines:
            if pattern.search(line):
                matched.append(line.strip())
            if len(matched) >= 5:
                break
        if matched:
            findings.append({"type": label, "evidence": matched})
    return findings


def run_command(project: Path, label: str, command: list[str], report_dir: Path) -> dict[str, Any]:
    report_dir.mkdir(parents=True, exist_ok=True)
    slug = f"{now_slug()}-{safe_slug(label)}"
    log_path = report_dir / f"{slug}.log"
    started = dt.datetime.now()
    process = subprocess.run(
        command,
        cwd=str(project),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    ended = dt.datetime.now()
    log_path.write_text(process.stdout or "", encoding="utf-8")
    data = {
        "kind": "command-run",
        "project": str(project.resolve()),
        "label": label,
        "command": command,
        "exit_code": process.returncode,
        "started_at": started.isoformat(timespec="seconds"),
        "ended_at": ended.isoformat(timespec="seconds"),
        "duration_seconds": round((ended - started).total_seconds(), 3),
        "log": str(log_path),
        "findings": classify_log(process.stdout or ""),
        "scan": scan_project(project),
    }
    write_report_pair(report_dir, slug, data)
    return data


def codex_env() -> dict[str, Any]:
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    skills_dir = codex_home / "skills"
    pets_dir = codex_home / "pets"
    skill_files = sorted(skills_dir.glob("*/SKILL.md")) if skills_dir.exists() else []
    pet_dirs = sorted([p for p in pets_dir.iterdir() if p.is_dir()]) if pets_dir.exists() else []
    skill_results = []
    for skill in skill_files:
        text = read_text_safe(skill, limit=30_000)
        name = re.search(r"^name:\s*(.+)$", text, re.M)
        description = re.search(r"^description:\s*(.+)$", text, re.M)
        skill_results.append({
            "dir": str(skill.parent),
            "name": name.group(1).strip() if name else None,
            "has_description": bool(description),
            "description_length": len(description.group(1).strip()) if description else 0,
        })
    return {
        "kind": "codex-env",
        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        "codex_home": str(codex_home),
        "skills_count": len(skill_results),
        "pets": [p.name for p in pet_dirs],
        "utoo_pet_installed": (pets_dir / "utoo" / "pet.json").exists(),
        "skills": skill_results,
    }


def write_report_pair(report_dir: Path, slug: str, data: dict[str, Any]) -> dict[str, str]:
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / f"{slug}.json"
    md_path = report_dir / f"{slug}.md"
    write_json(json_path, data)
    md_path.write_text(render_markdown(data), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def render_markdown(data: dict[str, Any]) -> str:
    lines = [
        f"# Utoo Watchdog Report: {data.get('kind', 'unknown')}",
        "",
        f"- Time: {data.get('timestamp') or data.get('ended_at') or ''}",
        f"- Project: `{data.get('project', '')}`",
    ]
    if data.get("kind") == "command-run":
        lines.extend([
            f"- Label: `{data.get('label')}`",
            f"- Command: `{' '.join(shlex.quote(x) for x in data.get('command', []))}`",
            f"- Exit code: `{data.get('exit_code')}`",
            f"- Duration: `{data.get('duration_seconds')}s`",
            f"- Log: `{data.get('log')}`",
        ])
    lines.append("")

    scan = data.get("scan") if data.get("kind") == "command-run" else data
    if isinstance(scan, dict) and scan.get("package_manager"):
        package = scan.get("package", {})
        pm = scan["package_manager"]
        lines.extend([
            "## Project Signals",
            "",
            f"- Family: `{', '.join(scan.get('family', {}).get('families', []))}`",
            f"- Package manager: `{pm.get('manager')}`",
            f"- Lockfiles: `{', '.join(pm.get('lockfiles', [])) or 'none'}`",
            f"- node_modules present: `{pm.get('node_modules')}`",
            f"- Package name: `{package.get('name')}`",
            "",
        ])
        if package.get("interesting_scripts"):
            lines.extend(["### Interesting Scripts", ""])
            for name, command in package["interesting_scripts"].items():
                lines.append(f"- `{name}`: `{command}`")
            lines.append("")
        if package.get("utoo_dependencies"):
            lines.extend(["### Utoo/Utoopack Dependencies", ""])
            for name, version in package["utoo_dependencies"].items():
                lines.append(f"- `{name}`: `{version}`")
            lines.append("")
        if scan.get("configs"):
            lines.extend(["### Config Matches", ""])
            for item in scan["configs"]:
                matches = ", ".join(item.get("matches", [])) or "no keyword match"
                lines.append(f"- `{item.get('path')}`: {matches}")
            lines.append("")

    if data.get("findings"):
        lines.extend(["## Failure Classification", ""])
        for finding in data["findings"]:
            lines.append(f"### {finding['type']}")
            for item in finding["evidence"]:
                lines.append(f"- `{item[:220]}`")
            lines.append("")

    recommendations = scan.get("recommendations", []) if isinstance(scan, dict) else []
    if recommendations:
        lines.extend(["## Static Recommendations", ""])
        for recommendation in recommendations:
            lines.append(f"- {recommendation}")
        lines.append("")

    if data.get("kind") == "codex-env":
        lines.extend([
            "## Codex Environment",
            "",
            f"- CODEX_HOME: `{data.get('codex_home')}`",
            f"- Utoo pet installed: `{data.get('utoo_pet_installed')}`",
            f"- Pets: `{', '.join(data.get('pets', []))}`",
            f"- Skills count: `{data.get('skills_count')}`",
            "",
        ])

    lines.extend([
        "## AI Handoff Prompt",
        "",
        "Use this report as evidence. Explain likely root cause, confidence, missing information, and next concrete commands or edits. If a command failed, inspect the referenced log before proposing a fix.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", default=None)
    sub = parser.add_subparsers(dest="command_name", required=True)

    scan = sub.add_parser("scan", help="Scan a project for utoopack and skill signals.")
    scan.add_argument("--project", default=".")
    scan.add_argument("--report-dir", default=None)

    run = sub.add_parser("run", help="Run and watch a build/install command.")
    run.add_argument("--project", default=".")
    run.add_argument("--label", default="task")
    run.add_argument("--report-dir", default=None)
    run.add_argument("cmd", nargs=argparse.REMAINDER)

    codex = sub.add_parser("codex", help="Inspect local Codex skills and pet state.")
    codex.add_argument("--report-dir", default=None)

    args = parser.parse_args()
    report_dir = Path(args.report_dir or "reports").expanduser()

    if args.command_name == "scan":
        data = scan_project(Path(args.project))
        paths = write_report_pair(report_dir, f"{now_slug()}-scan", data)
        print(json.dumps({"ok": True, "report": paths, "summary": data}, ensure_ascii=False, indent=2))
        return 0

    if args.command_name == "run":
        command = args.cmd
        if command and command[0] == "--":
            command = command[1:]
        if not command:
            print("Missing command after --", file=sys.stderr)
            return 2
        data = run_command(Path(args.project).resolve(), args.label, command, report_dir)
        print(json.dumps({"ok": data["exit_code"] == 0, "exit_code": data["exit_code"], "log": data["log"]}, ensure_ascii=False, indent=2))
        return data["exit_code"]

    if args.command_name == "codex":
        data = codex_env()
        paths = write_report_pair(report_dir, f"{now_slug()}-codex", data)
        print(json.dumps({"ok": True, "report": paths, "summary": data}, ensure_ascii=False, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
