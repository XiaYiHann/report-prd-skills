#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${RESEARCH_LOOP_REPO_URL:-${RESEARCH_EXECUTION_SKILLS_REPO_URL:-${REPORT_PRD_SKILLS_REPO_URL:-https://github.com/XiaYiHann/research-loop.git}}}"
REPO_REF="${RESEARCH_LOOP_REPO_REF:-${RESEARCH_EXECUTION_SKILLS_REF:-${REPORT_PRD_SKILLS_REF:-main}}}"
CACHE_DIR="${RESEARCH_LOOP_CACHE_DIR:-${HOME}/.claude/research-loop}"
SOURCE_DIR="${RESEARCH_EXECUTION_SKILLS_SOURCE_DIR:-${RESEARCH_LOOP_SOURCE_DIR:-${REPORT_PRD_SKILLS_SOURCE_DIR:-}}}"
SKILLS_TARGET_DIR="${RESEARCH_EXECUTION_SKILLS_TARGET_DIR:-${RESEARCH_LOOP_SKILLS_DIR:-${CLAUDE_SKILLS_DIR:-${HOME}/.claude/skills}}}"
PROJECT_AGENTS_TARGET_DIR="${RESEARCH_EXECUTION_SUBAGENTS_TARGET_DIR:-${RESEARCH_LOOP_PROJECT_AGENTS_DIR:-.claude/agents}}"
USER_AGENTS_TARGET_DIR="${RESEARCH_EXECUTION_USER_AGENTS_TARGET_DIR:-${RESEARCH_LOOP_USER_AGENTS_DIR:-${HOME}/.claude/agents}}"

INSTALL_SKILLS=true
INSTALL_AGENTS=true
AGENTS_SCOPE="project"
INIT_WORKSPACE=false
FORCE=false
DRY_RUN=false

SKILLS=(
  research
  research-explore
  research-init
  research-prd
  research-paper
  research-spec
  research-plan
  research-audit
  research-ppt
)

CLAUDE_SUBAGENTS=(
  research-math
  research-literature
  research-reproduce
  research-coding
  research-experiment
  research-analysis
  research-paper
  research-ppt
  research-audit
)

usage() {
  cat <<'EOF'
Usage: install.sh [options]

Installs the research-loop skill family for Claude Code. By default it installs
research skills into ~/.claude/skills and project-level subagents into
./.claude/agents. It does not initialize docs/research unless requested.

Options:
  --init-workspace   create the docs/research epoch scaffold
  --no-agents        install skills only; do not install subagents
  --project-agents   install subagents into ./.claude/agents (default)
  --user-agents      install subagents into ~/.claude/agents
  --skills-only      install skills only
  --agents-only      install subagents only
  --force            overwrite existing destination files/directories
  --dry-run          print planned actions without cloning, copying, or mkdir
  --help             show this help

Compatibility:
  --with-subagents   accepted as an alias for --project-agents

Environment:
  RESEARCH_LOOP_REPO_URL                    default: https://github.com/XiaYiHann/research-loop.git
  RESEARCH_LOOP_REPO_REF                    default: main
  RESEARCH_LOOP_CACHE_DIR                   default: ~/.claude/research-loop
  RESEARCH_EXECUTION_SKILLS_SOURCE_DIR      install from local checkout
  RESEARCH_EXECUTION_SKILLS_TARGET_DIR      default: ~/.claude/skills
  RESEARCH_EXECUTION_SUBAGENTS_TARGET_DIR   default: ./.claude/agents
  RESEARCH_EXECUTION_USER_AGENTS_TARGET_DIR default: ~/.claude/agents
EOF
}

log() {
  printf '[research-loop] %s\n' "$*"
}

die() {
  printf '[research-loop] error: %s\n' "$*" >&2
  exit 1
}

while (( "$#" )); do
  case "$1" in
    --init-workspace)
      INIT_WORKSPACE=true
      shift
      ;;
    --no-agents|--skills-only)
      INSTALL_AGENTS=false
      INSTALL_SKILLS=true
      shift
      ;;
    --project-agents|--with-subagents)
      INSTALL_AGENTS=true
      AGENTS_SCOPE="project"
      shift
      ;;
    --user-agents)
      INSTALL_AGENTS=true
      AGENTS_SCOPE="user"
      shift
      ;;
    --agents-only)
      INSTALL_AGENTS=true
      INSTALL_SKILLS=false
      shift
      ;;
    --force)
      FORCE=true
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

run_mkdir() {
  local dir="$1"
  if [[ "$DRY_RUN" == "true" ]]; then
    log "DRY RUN: would create directory $dir"
    return
  fi
  mkdir -p "$dir"
}

copy_path() {
  local source="$1"
  local dest="$2"
  local label="$3"
  local kind="$4"

  if [[ -e "$dest" || -L "$dest" ]]; then
    if [[ "$FORCE" == "true" ]]; then
      if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: would overwrite $label at $dest"
        return
      fi
      rm -rf "$dest"
      cp -R "$source" "$dest"
      log "$label overwritten"
      return
    fi
    log "$label exists, skipped"
    return
  fi

  if [[ "$DRY_RUN" == "true" ]]; then
    log "DRY RUN: would install $kind $label -> $dest"
    return
  fi
  cp -R "$source" "$dest"
  log "$label installed"
}

resolve_source_dir() {
  if [[ -n "$SOURCE_DIR" ]]; then
    printf '%s\n' "$SOURCE_DIR"
    return
  fi

  local script_path="${BASH_SOURCE[0]:-}"
  if [[ -n "$script_path" && -f "$script_path" ]]; then
    local script_dir
    script_dir="$(cd "$(dirname "$script_path")" && pwd)"
    if [[ -f "$script_dir/skills/research/SKILL.md" ]]; then
      printf '%s\n' "$script_dir"
      return
    fi
  fi

  if [[ "$DRY_RUN" == "true" ]]; then
    printf '%s\n' "$CACHE_DIR"
    return
  fi

  command -v git >/dev/null 2>&1 || die "git is required when installing from the remote one-line command"
  mkdir -p "$(dirname "$CACHE_DIR")"
  if [[ -d "$CACHE_DIR/.git" ]]; then
    log "Updating $CACHE_DIR from $REPO_URL#$REPO_REF" >&2
    git -C "$CACHE_DIR" fetch --depth 1 origin "$REPO_REF" >/dev/null
    git -C "$CACHE_DIR" checkout -q FETCH_HEAD
  else
    if [[ -e "$CACHE_DIR" ]]; then
      die "cache path exists but is not a git checkout: $CACHE_DIR"
    fi
    log "Cloning $REPO_URL#$REPO_REF into $CACHE_DIR" >&2
    git clone --depth 1 --branch "$REPO_REF" "$REPO_URL" "$CACHE_DIR" >/dev/null
  fi
  printf '%s\n' "$CACHE_DIR"
}

SOURCE_DIR="$(resolve_source_dir)"
if [[ "$DRY_RUN" == "true" ]]; then
  log "DRY RUN: source would be $SOURCE_DIR"
else
  SOURCE_DIR="$(cd "$SOURCE_DIR" && pwd)"
  [[ -d "$SOURCE_DIR/skills" ]] || die "source directory does not contain skills/: $SOURCE_DIR"
  [[ -d "$SOURCE_DIR/agents/claude-code" ]] || die "source directory does not contain agents/claude-code/: $SOURCE_DIR"
fi

if [[ "$INSTALL_SKILLS" == "true" ]]; then
  run_mkdir "$SKILLS_TARGET_DIR"
  if [[ "$DRY_RUN" != "true" ]]; then
    SKILLS_TARGET_DIR="$(cd "$SKILLS_TARGET_DIR" && pwd)"
  fi
  log "Installed research-loop skills:"
  for skill in "${SKILLS[@]}"; do
    if [[ "$DRY_RUN" != "true" ]]; then
      [[ -f "$SOURCE_DIR/skills/$skill/SKILL.md" ]] || die "missing required skill: $skill"
    fi
    copy_path "$SOURCE_DIR/skills/$skill" "$SKILLS_TARGET_DIR/$skill" "$skill" "skill"
  done
else
  log "Skills installation skipped."
fi

AGENTS_TARGET_DIR="$PROJECT_AGENTS_TARGET_DIR"
if [[ "$AGENTS_SCOPE" == "user" ]]; then
  AGENTS_TARGET_DIR="$USER_AGENTS_TARGET_DIR"
fi

if [[ "$INSTALL_AGENTS" == "true" ]]; then
  run_mkdir "$AGENTS_TARGET_DIR"
  if [[ "$DRY_RUN" != "true" ]]; then
    AGENTS_TARGET_DIR="$(cd "$AGENTS_TARGET_DIR" && pwd)"
  fi
  log "Installed Claude Code subagents:"
  for agent in "${CLAUDE_SUBAGENTS[@]}"; do
    if [[ "$DRY_RUN" != "true" ]]; then
      [[ -f "$SOURCE_DIR/agents/claude-code/$agent.md" ]] || die "missing Claude Code subagent template: $agent"
    fi
    copy_path "$SOURCE_DIR/agents/claude-code/$agent.md" "$AGENTS_TARGET_DIR/$agent.md" "$agent" "agent"
  done
else
  log "Claude Code subagents skipped."
fi

if [[ "$INIT_WORKSPACE" == "true" ]]; then
  log "Workspace scaffold:"
  if [[ "$DRY_RUN" == "true" ]]; then
    log "would initialize docs/research with Charter-bounded epoch scaffold"
  else
    INIT_ARGS=(--repo "$PWD" --title "$(basename "$PWD")" --purpose "initial-research-scaffold")
    if [[ "$FORCE" == "true" ]]; then
      INIT_ARGS+=(--force)
    fi
    python3 "$SOURCE_DIR/skills/research-init/scripts/init_research.py" "${INIT_ARGS[@]}"
  fi
else
  log "Workspace scaffold not initialized. Pass --init-workspace to create docs/research directories."
fi

cat <<'EOF'

Next steps:
1. Open Claude Code in your project.
2. Run `/research-init` or `/research`.
3. Complete and approve `docs/research/prd/research_prd.md`.
4. Run `/research` to continue the autonomous loop.
EOF
