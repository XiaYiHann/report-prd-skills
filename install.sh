#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${RESEARCH_EXECUTION_SKILLS_REPO_URL:-${REPORT_PRD_SKILLS_REPO_URL:-https://github.com/XiaYiHann/research-loop.git}}"
REPO_REF="${RESEARCH_EXECUTION_SKILLS_REF:-${REPORT_PRD_SKILLS_REF:-main}}"
TARGET_DIR="${RESEARCH_EXECUTION_SKILLS_TARGET_DIR:-${REPORT_PRD_SKILLS_TARGET_DIR:-${HOME}/.agents/skills}}"
CLAUDE_TARGET_DIR="${RESEARCH_EXECUTION_SKILLS_CLAUDE_TARGET_DIR:-${CLAUDE_SKILLS_DIR:-${HOME}/.claude/skills}}"
SOURCE_DIR="${RESEARCH_EXECUTION_SKILLS_SOURCE_DIR:-${REPORT_PRD_SKILLS_SOURCE_DIR:-}}"

SKILLS=(
  report
  research
  research-init
  research-prd
  research-paper
  research-spec
  research-plan
  research-audit
  research-ppt
)

LEGACY_REPORT_SKILLS=(
  report-init
  report-brainstorming
  report-update
  report-audit
  report-goal
  report-paper
  report-spec
  report-debate
  report-paper-plan
  report-paper-draft
  report-ingest-results
)

OBSOLETE_RESEARCH_SKILLS=(
  research-evidence
  research-writing
  research-goal
)

OBSOLETE_SKILLS=(
  "${LEGACY_REPORT_SKILLS[@]}"
  "${OBSOLETE_RESEARCH_SKILLS[@]}"
)

CLAUDE_LINK_SKILLS=(
  research
  research-init
  research-prd
  research-paper
  research-spec
  research-plan
  research-audit
  research-ppt
)

log() {
  printf '[research-execution-skills] %s\n' "$*"
}

die() {
  printf '[research-execution-skills] error: %s\n' "$*" >&2
  exit 1
}

resolve_source_dir() {
  if [[ -n "$SOURCE_DIR" ]]; then
    printf 'local:%s\n' "$SOURCE_DIR"
    return
  fi

  local script_path="${BASH_SOURCE[0]:-}"
  local script_dir=""
  if [[ -n "$script_path" && -f "$script_path" ]]; then
    script_dir="$(cd "$(dirname "$script_path")" && pwd)"
    if [[ -f "$script_dir/skills/research-init/SKILL.md" ]]; then
      printf 'local:%s\n' "$script_dir"
      return
    fi
  fi

  command -v git >/dev/null 2>&1 || die "git is required when installing from the remote one-line command"

  local tmp_dir
  tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/research-execution-skills.XXXXXX")"
  log "Cloning $REPO_URL#$REPO_REF" >&2
  git clone --depth 1 --branch "$REPO_REF" "$REPO_URL" "$tmp_dir" >/dev/null
  printf 'clone:%s\n' "$tmp_dir"
}

SOURCE_RESOLUTION="$(resolve_source_dir)"
SOURCE_KIND="${SOURCE_RESOLUTION%%:*}"
SOURCE_DIR="${SOURCE_RESOLUTION#*:}"
if [[ "$SOURCE_KIND" == "clone" ]]; then
  trap 'rm -rf "$SOURCE_DIR"' EXIT
fi
SOURCE_DIR="$(cd "$SOURCE_DIR" && pwd)"

[[ -d "$SOURCE_DIR/skills" ]] || die "source directory does not contain skills/: $SOURCE_DIR"

for skill in "${SKILLS[@]}"; do
  [[ -f "$SOURCE_DIR/skills/$skill/SKILL.md" ]] || die "missing required skill: $skill"
done

mkdir -p "$TARGET_DIR"
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

log "Installing into $TARGET_DIR"

MIGRATED_SKILLS=()

for skill in "${SKILLS[@]}"; do
  if [[ -e "$TARGET_DIR/$skill" || -L "$TARGET_DIR/$skill" ]]; then
    if [[ "$skill" == "report" ]]; then
      MIGRATED_SKILLS+=("$skill -> legacy research migration router")
    fi
    rm -rf "$TARGET_DIR/$skill"
  fi
done

for skill in "${OBSOLETE_SKILLS[@]}"; do
  if [[ -e "$TARGET_DIR/$skill" || -L "$TARGET_DIR/$skill" ]]; then
    MIGRATED_SKILLS+=("$skill -> removed")
    rm -rf "$TARGET_DIR/$skill"
  fi
done

for skill in "${SKILLS[@]}"; do
  cp -R "$SOURCE_DIR/skills/$skill" "$TARGET_DIR/$skill"
done

if (( ${#MIGRATED_SKILLS[@]} > 0 )); then
  log "Migrated existing skill directories to research-*:"
  for item in "${MIGRATED_SKILLS[@]}"; do
    printf '  - %s\n' "$item"
  done
else
  log "No legacy report skill directories found; installed research-* cleanly."
fi

log "Installed research execution skill family:"
for skill in "${SKILLS[@]}"; do
  printf '  - %s\n' "$skill"
done

mkdir -p "$CLAUDE_TARGET_DIR"
CLAUDE_TARGET_DIR="$(cd "$CLAUDE_TARGET_DIR" && pwd)"

if [[ "$CLAUDE_TARGET_DIR" == "$TARGET_DIR" ]]; then
  log "Claude skills target is the same as install target; symlink step skipped."
else
  log "Linked research skills for Claude Code into $CLAUDE_TARGET_DIR:"
  for skill in "${CLAUDE_LINK_SKILLS[@]}"; do
    [[ -d "$TARGET_DIR/$skill" ]] || die "cannot link missing installed skill: $TARGET_DIR/$skill"
    if [[ -e "$CLAUDE_TARGET_DIR/$skill" || -L "$CLAUDE_TARGET_DIR/$skill" ]]; then
      rm -rf "$CLAUDE_TARGET_DIR/$skill"
    fi
    ln -s "$TARGET_DIR/$skill" "$CLAUDE_TARGET_DIR/$skill"
    printf '  - %s -> %s\n' "$skill" "$TARGET_DIR/$skill"
  done
fi

log "Done. Restart Codex if it does not pick up the updated skills immediately."
