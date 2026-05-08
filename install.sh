#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPORT_PRD_SKILLS_REPO_URL:-https://github.com/XiaYiHann/report-prd-skills.git}"
REPO_REF="${REPORT_PRD_SKILLS_REF:-main}"
TARGET_DIR="${REPORT_PRD_SKILLS_TARGET_DIR:-${HOME}/.agents/skills}"
SOURCE_DIR="${REPORT_PRD_SKILLS_SOURCE_DIR:-}"

SKILLS=(
  report
  report-init
  report-brainstorming
  report-update
  report-audit
  report-goal
  report-paper
)

OBSOLETE_SKILLS=(
  report-debate
  report-paper-plan
  report-paper-draft
  report-ingest-results
  report-spec
)

log() {
  printf '[report-prd-skills] %s\n' "$*"
}

die() {
  printf '[report-prd-skills] error: %s\n' "$*" >&2
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
    if [[ -f "$script_dir/skills/report/SKILL.md" ]]; then
      printf 'local:%s\n' "$script_dir"
      return
    fi
  fi

  command -v git >/dev/null 2>&1 || die "git is required when installing from the remote one-line command"

  local tmp_dir
  tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/report-prd-skills.XXXXXX")"
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

for skill in "${SKILLS[@]}" "${OBSOLETE_SKILLS[@]}"; do
  if [[ -e "$TARGET_DIR/$skill" || -L "$TARGET_DIR/$skill" ]]; then
    rm -rf "$TARGET_DIR/$skill"
  fi
done

for skill in "${SKILLS[@]}"; do
  cp -R "$SOURCE_DIR/skills/$skill" "$TARGET_DIR/$skill"
done

log "Installed report skill family:"
for skill in "${SKILLS[@]}"; do
  printf '  - %s\n' "$skill"
done

log "Done. Restart Codex if it does not pick up the updated skills immediately."
