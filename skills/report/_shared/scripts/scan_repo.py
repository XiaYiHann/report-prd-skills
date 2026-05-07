#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path


IGNORE_DIRS = {
    ".git",
    ".worktrees",
    ".venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".ruff_cache",
    ".playwright-mcp",
    "dist",
    "build",
    "coverage",
}

GENERATED_SUFFIXES = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".aux",
    ".log",
    ".out",
    ".bbl",
    ".blg",
    ".fls",
    ".fdb_latexmk",
    ".zip",
}


@dataclass
class FileSignal:
    path: str
    score: int
    category: str
    reason: str
    signals: list[str]


@dataclass
class ModuleCandidate:
    name: str
    source_paths: list[str]
    entrypoints: list[str]
    test_paths: list[str]
    component_signals: list[str]
    reason: str


def is_noise(path: Path) -> bool:
    if any(part in IGNORE_DIRS for part in path.parts):
        return True
    if path.suffix.lower() in GENERATED_SUFFIXES:
        return True
    return False


def category_for(path: Path) -> tuple[str, int, str]:
    text = path.as_posix().lower()
    name = path.name.lower()

    if re.match(r"readme", name):
        return "docs", 95, "Top-level project narrative"
    if "docs/" in text and ("spec" in text or "plan" in text or "architecture" in text):
        return "docs", 92, "Structured design or planning document"
    if path.suffix == ".tex":
        return "paper", 90, "Paper or report source"
    if "/simulation/" in text or text.startswith("simulation/"):
        return "code", 90, "Core experiment or simulation entrypoint"
    if "/src/" in text or "/app/" in text or "/packages/" in text:
        return "code", 88, "Likely product or library source"
    if "/tests/" in text or text.startswith("tests/"):
        return "tests", 86, "Behavior constraints and regression expectations"
    if name in {"requirements.txt", "pyproject.toml", "package.json", "go.mod", "cargo.toml", "pytest.ini"}:
        return "config", 82, "Dependency or execution configuration"
    if path.suffix in {".md", ".rst"}:
        return "docs", 80, "General documentation"
    return "other", 50, "Potentially useful project file"


def extract_signals(path: Path) -> list[str]:
    try:
        text = path.read_text(errors="ignore")
    except Exception:
        return []

    signals: list[str] = []
    if path.suffix in {".md", ".rst"}:
        signals.extend(re.findall(r"^#{1,3}\s+(.+)$", text, re.MULTILINE)[:4])
    elif path.suffix == ".py":
        signals.extend(re.findall(r"^(?:def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", text, re.MULTILINE)[:6])
    elif path.suffix == ".tex":
        signals.extend(re.findall(r"\\(?:section|subsection)\{([^}]+)\}", text)[:6])
    return signals


def is_source_file(path: Path) -> bool:
    return path.suffix.lower() in {
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".go",
        ".rs",
        ".java",
        ".kt",
    }


def module_name_for_path(path: Path) -> str | None:
    parts = path.parts
    if not parts or not is_source_file(path):
        return None

    if parts[0] in {"apps", "packages"} and len(parts) >= 3:
        return parts[1]
    if parts[0] == "src":
        if len(parts) >= 3:
            return parts[1]
        return path.stem
    if parts[0] in {"simulation", "scripts"}:
        if len(parts) >= 3:
            return parts[1]
        return parts[0]
    return None


def is_entrypoint(path: Path) -> bool:
    name = path.name.lower()
    return name in {
        "__init__.py",
        "main.py",
        "app.py",
        "index.ts",
        "index.tsx",
        "index.js",
        "page.tsx",
        "route.ts",
    } or any(token in name for token in ("service", "worker", "task", "cli"))


def related_tests(module_name: str, findings: list[FileSignal]) -> list[str]:
    lowered_name = module_name.lower()
    tests: list[str] = []
    for item in findings:
        path = item.path.lower()
        if "/tests/" not in f"/{path}" and not path.startswith("tests/"):
            continue
        if lowered_name in path:
            tests.append(item.path)
    return sorted(tests)[:6]


def collect_module_candidates(findings: list[FileSignal]) -> list[ModuleCandidate]:
    grouped: dict[str, list[FileSignal]] = {}
    for item in findings:
        path = Path(item.path)
        module_name = module_name_for_path(path)
        if module_name is None:
            continue
        grouped.setdefault(module_name, []).append(item)

    candidates: list[ModuleCandidate] = []
    for name, items in grouped.items():
        source_paths = sorted(item.path for item in items)[:8]
        entrypoints = sorted(item.path for item in items if is_entrypoint(Path(item.path)))[:4]
        component_signals: list[str] = []
        for item in items:
            component_signals.extend(item.signals)
        candidates.append(
            ModuleCandidate(
                name=name,
                source_paths=source_paths,
                entrypoints=entrypoints,
                test_paths=related_tests(name, findings),
                component_signals=component_signals[:8],
                reason=f"Detected from `{name}` source layout under apps/packages/src/simulation/scripts.",
            )
        )

    candidates.sort(key=lambda item: (-len(item.source_paths), item.name))
    return candidates[:8]


def collect(repo_path: Path) -> dict[str, object]:
    findings: list[FileSignal] = []

    for root, dirs, files in os.walk(repo_path):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for filename in files:
            path = root_path / filename
            rel = path.relative_to(repo_path)
            if is_noise(rel):
                continue

            category, score, reason = category_for(rel)
            findings.append(
                FileSignal(
                    path=rel.as_posix(),
                    score=score,
                    category=category,
                    reason=reason,
                    signals=extract_signals(path),
                )
            )

    findings.sort(key=lambda item: (-item.score, item.path))

    priority_dirs: dict[str, int] = {}
    for item in findings[:30]:
        top = item.path.split("/", 1)[0]
        priority_dirs[top] = max(priority_dirs.get(top, 0), item.score)

    sorted_dirs = sorted(priority_dirs.items(), key=lambda kv: (-kv[1], kv[0]))
    return {
        "repo": str(repo_path),
        "recommended_targets": [asdict(item) for item in findings[:15]],
        "module_candidates": [asdict(item) for item in collect_module_candidates(findings)],
        "priority_paths": [name for name, _ in sorted_dirs[:10]],
        "noise_paths": sorted(IGNORE_DIRS),
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines = ["# Repo Report Scan", ""]
    lines.append(f"仓库: `{payload['repo']}`")
    lines.append("")
    lines.append("## 推荐提取目标")
    lines.append("")
    for item in payload["recommended_targets"]:
        signals = ", ".join(item["signals"]) if item["signals"] else "无显式结构信号"
        lines.append(f"- `{item['path']}`: {item['reason']}。信号: {signals}")
    lines.append("")
    lines.append("## 候选模块")
    lines.append("")
    for item in payload.get("module_candidates", []):
        sources = ", ".join(item["source_paths"]) if item["source_paths"] else "无源码线索"
        tests = ", ".join(item["test_paths"]) if item["test_paths"] else "无测试线索"
        lines.append(f"- `{item['name']}`: source={sources}; tests={tests}")
    lines.append("")
    lines.append("## 优先扫描路径")
    lines.append("")
    for path in payload["priority_paths"]:
        lines.append(f"- `{path}`")
    lines.append("")
    lines.append("## 可能的噪音路径")
    lines.append("")
    for path in payload["noise_paths"]:
        lines.append(f"- `{path}`")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Produce a repo scan summary for report writing.")
    parser.add_argument("repo_path", help="Path to the repository to scan.")
    parser.add_argument("--format", choices=["md", "json"], default="md", help="Output format.")
    parser.add_argument("--output", help="Optional output file path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_path = Path(args.repo_path).resolve()
    if not repo_path.exists():
        print(f"[ERROR] Repo not found: {repo_path}")
        return 1

    payload = collect(repo_path)
    text = render_markdown(payload) if args.format == "md" else json.dumps(payload, ensure_ascii=False, indent=2)

    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text)
        print(f"[OK] Wrote scan output: {output_path}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
