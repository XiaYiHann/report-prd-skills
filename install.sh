#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${RESEARCH_LOOP_REPO_URL:-${RESEARCH_EXECUTION_SKILLS_REPO_URL:-${REPORT_PRD_SKILLS_REPO_URL:-https://github.com/XiaYiHann/research-loop.git}}}"
REPO_REF="${RESEARCH_LOOP_REPO_REF:-${RESEARCH_EXECUTION_SKILLS_REF:-${REPORT_PRD_SKILLS_REF:-main}}}"
CACHE_DIR="${RESEARCH_LOOP_CACHE_DIR:-${HOME}/.claude/research-loop}"
SOURCE_DIR="${RESEARCH_EXECUTION_SKILLS_SOURCE_DIR:-${RESEARCH_LOOP_SOURCE_DIR:-${REPORT_PRD_SKILLS_SOURCE_DIR:-}}}"
AGENTS_SKILLS_DIR="${RESEARCH_LOOP_AGENTS_SKILLS_DIR:-${AGENTS_SKILLS_DIR:-${HOME}/.agents/skills}}"
SKILLS_TARGET_DIR="${RESEARCH_EXECUTION_SKILLS_TARGET_DIR:-${RESEARCH_LOOP_SKILLS_DIR:-$AGENTS_SKILLS_DIR}}"
CLAUDE_SKILLS_LINK="${RESEARCH_LOOP_CLAUDE_SKILLS_DIR:-${CLAUDE_SKILLS_DIR:-${HOME}/.claude/skills}}"
PROJECT_AGENTS_TARGET_DIR="${RESEARCH_EXECUTION_SUBAGENTS_TARGET_DIR:-${RESEARCH_LOOP_PROJECT_AGENTS_DIR:-.claude/agents}}"
USER_AGENTS_TARGET_DIR="${RESEARCH_EXECUTION_USER_AGENTS_TARGET_DIR:-${RESEARCH_LOOP_USER_AGENTS_DIR:-${HOME}/.claude/agents}}"

INSTALL_SKILLS=true
INSTALL_AGENTS=true
AGENTS_SCOPE="user"
INIT_WORKSPACE=false
FORCE=false
DRY_RUN=false

SKILLS=(
  research
  research-explore
  research-insight
  research-status
  research-init
  research-goal
  research-audit
)

INTERNAL_COMPILER_MODULES=(
  research-paper
  research-spec
  research-plan
)

RETIRED_SKILL_ENTRIES=(
  research-prd
  research-ppt
  research-evidence
  research-writing
  research-brainstorming
)

CLAUDE_SUBAGENTS=(
  research-math
  research-literature
  research-reproduce
  research-coding
  research-experiment
  research-analysis
  research-paper
  research-audit
)

usage() {
  cat <<'EOF'
Usage: install.sh [options]

Installs the research-loop skill family for Claude Code. By default it installs
research skills into ~/.agents/skills, keeps ~/.claude/skills as a symlink to
that canonical store, and installs user-level subagents into ~/.claude/agents.
It does not initialize docs/research unless requested.

Options:
  --init-workspace   create the docs/research epoch scaffold
  --no-agents        install skills only; do not install subagents
  --user-agents      install subagents into ~/.claude/agents (default)
  --project-agents   install subagents into ./.claude/agents
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
  RESEARCH_EXECUTION_SKILLS_TARGET_DIR      default: ~/.agents/skills
  RESEARCH_LOOP_AGENTS_SKILLS_DIR           default: ~/.agents/skills canonical store
  RESEARCH_LOOP_CLAUDE_SKILLS_DIR           default: ~/.claude/skills symlink
  RESEARCH_EXECUTION_USER_AGENTS_TARGET_DIR default: ~/.claude/agents
  RESEARCH_EXECUTION_SUBAGENTS_TARGET_DIR   default: ./.claude/agents
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

copy_internal_module() {
  local module="$1"
  local source="$SOURCE_DIR/skills/$module"
  local dest="$SKILLS_TARGET_DIR/$module"

  if [[ "$DRY_RUN" != "true" ]]; then
    [[ -d "$source" ]] || die "missing internal compiler module: $module"
  fi

  copy_path "$source" "$dest" "$module" "internal compiler module"

  local stale_skill="$dest/SKILL.md"
  if [[ "$DRY_RUN" == "true" ]]; then
    log "DRY RUN: would remove retired user-facing skill entry $stale_skill if present"
  elif [[ -f "$stale_skill" ]]; then
    rm -f "$stale_skill"
    log "$module retired SKILL.md removed"
  fi
  if [[ "$DRY_RUN" != "true" && -d "$dest" && "$FORCE" != "true" ]]; then
    cp -Rn "$source/." "$dest"
  fi
}

remove_managed_skill_path() {
  local root="$1"
  local skill="$2"
  local path="$root/$skill"
  if [[ "$DRY_RUN" == "true" ]]; then
    log "DRY RUN: would remove retired user-facing skill path $path if present"
  elif [[ -e "$path" || -L "$path" ]]; then
    rm -rf "$path"
    log "$skill retired skill path removed from $root"
  fi
}

remove_retired_skill_entry() {
  local skill="$1"
  remove_managed_skill_path "$SKILLS_TARGET_DIR" "$skill"
}

remove_retired_skill_entries_from() {
  local root="$1"
  for retired_skill in "${RETIRED_SKILL_ENTRIES[@]}"; do
    remove_managed_skill_path "$root" "$retired_skill"
  done
}

remove_research_loop_entries_for_reinstall() {
  local root="$1"
  for skill in "${SKILLS[@]}"; do
    remove_managed_skill_path "$root" "$skill"
  done
  for module in "${INTERNAL_COMPILER_MODULES[@]}"; do
    remove_managed_skill_path "$root" "$module"
  done
  remove_retired_skill_entries_from "$root"
}

same_physical_dir() {
  local left="$1"
  local right="$2"
  if [[ "$DRY_RUN" == "true" ]]; then
    [[ "$left" == "$right" ]]
    return
  fi
  [[ -d "$left" && -d "$right" ]] || return 1
  [[ "$(cd "$left" && pwd -P)" == "$(cd "$right" && pwd -P)" ]]
}

migrate_skill_dir_entries() {
  local source_dir="$1"
  local dest_dir="$2"
  [[ -d "$source_dir" && ! -L "$source_dir" ]] || return

  shopt -s nullglob dotglob
  local entry
  for entry in "$source_dir"/*; do
    local name
    name="$(basename "$entry")"
    [[ "$name" == "." || "$name" == ".." ]] && continue
    if [[ ! -e "$dest_dir/$name" && ! -L "$dest_dir/$name" ]]; then
      mv "$entry" "$dest_dir/$name"
    fi
  done
  shopt -u nullglob dotglob
}

ensure_claude_skills_symlink() {
  if [[ "$DRY_RUN" == "true" ]]; then
    log "DRY RUN: would make $CLAUDE_SKILLS_LINK a symlink to $SKILLS_TARGET_DIR"
    return
  fi

  if [[ "$CLAUDE_SKILLS_LINK" == "$SKILLS_TARGET_DIR" ]]; then
    log "Claude skills path is the canonical skills store"
    return
  fi

  mkdir -p "$(dirname "$CLAUDE_SKILLS_LINK")"
  if [[ -L "$CLAUDE_SKILLS_LINK" ]]; then
    if [[ "$(readlink -f "$CLAUDE_SKILLS_LINK")" == "$(cd "$SKILLS_TARGET_DIR" && pwd -P)" ]]; then
      log "$CLAUDE_SKILLS_LINK already points to canonical skills store"
      return
    fi
    rm "$CLAUDE_SKILLS_LINK"
  elif [[ -e "$CLAUDE_SKILLS_LINK" ]]; then
    if same_physical_dir "$CLAUDE_SKILLS_LINK" "$SKILLS_TARGET_DIR"; then
      log "Claude skills path already resolves to canonical skills store"
      return
    fi
    migrate_skill_dir_entries "$CLAUDE_SKILLS_LINK" "$SKILLS_TARGET_DIR"
    rm -rf "$CLAUDE_SKILLS_LINK"
  fi

  ln -s "$SKILLS_TARGET_DIR" "$CLAUDE_SKILLS_LINK"
  log "Linked $CLAUDE_SKILLS_LINK -> $SKILLS_TARGET_DIR"
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
  ensure_claude_skills_symlink
  if [[ "$FORCE" == "true" ]]; then
    log "Removing existing research-loop managed skill entries before reinstall"
    remove_research_loop_entries_for_reinstall "$SKILLS_TARGET_DIR"
  else
    remove_retired_skill_entries_from "$SKILLS_TARGET_DIR"
  fi
  log "Installed research-loop skills:"
  for skill in "${SKILLS[@]}"; do
    if [[ "$DRY_RUN" != "true" ]]; then
      [[ -f "$SOURCE_DIR/skills/$skill/SKILL.md" ]] || die "missing required skill: $skill"
    fi
    copy_path "$SOURCE_DIR/skills/$skill" "$SKILLS_TARGET_DIR/$skill" "$skill" "skill"
  done
  log "Installed internal compiler modules:"
  for module in "${INTERNAL_COMPILER_MODULES[@]}"; do
    copy_internal_module "$module"
  done
  remove_retired_skill_entries_from "$SKILLS_TARGET_DIR"
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
1. 打开 Claude Code。
2. 若 workspace 不存在，AI 会自动运行 research-init 初始化（阶段 0）。
3. 与 AI 讨论你的研究方向，AI 会逐章填写 PRD（阶段 1）。
4. 审阅并批准 PRD，AI 将自动执行所有 Gate（阶段 2）。
5. 也可以手动启动：/research
EOF
