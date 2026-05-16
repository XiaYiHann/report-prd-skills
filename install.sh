#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${RESEARCH_LOOP_REPO_URL:-${RESEARCH_EXECUTION_SKILLS_REPO_URL:-${REPORT_PRD_SKILLS_REPO_URL:-https://github.com/XiaYiHann/research-loop.git}}}"
REPO_REF="${RESEARCH_LOOP_REPO_REF:-${RESEARCH_EXECUTION_SKILLS_REF:-${REPORT_PRD_SKILLS_REF:-main}}}"
CACHE_DIR="${RESEARCH_LOOP_CACHE_DIR:-${HOME}/.claude/research-loop}"
SOURCE_DIR="${RESEARCH_EXECUTION_SKILLS_SOURCE_DIR:-${RESEARCH_LOOP_SOURCE_DIR:-${REPORT_PRD_SKILLS_SOURCE_DIR:-}}}"
SKILLS_TARGET_DIR="${RESEARCH_EXECUTION_SKILLS_TARGET_DIR:-${RESEARCH_LOOP_SKILLS_DIR:-${CLAUDE_SKILLS_DIR:-${HOME}/.claude/skills}}}"
AGENTS_SKILLS_DIR="${RESEARCH_LOOP_AGENTS_SKILLS_DIR:-${AGENTS_SKILLS_DIR:-${HOME}/.agents/skills}}"
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
research skills into ~/.claude/skills and user-level subagents into
~/.claude/agents. It does not initialize docs/research unless requested.

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
  RESEARCH_EXECUTION_SKILLS_TARGET_DIR      default: ~/.claude/skills
  RESEARCH_LOOP_AGENTS_SKILLS_DIR           default: ~/.agents/skills compatibility links
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

materialize_skills_target_if_agents_backed() {
  if [[ "$DRY_RUN" == "true" || ! -L "$SKILLS_TARGET_DIR" ]]; then
    return
  fi

  run_mkdir "$AGENTS_SKILLS_DIR"
  local skills_real
  local agents_real
  skills_real="$(cd "$SKILLS_TARGET_DIR" && pwd -P)"
  agents_real="$(cd "$AGENTS_SKILLS_DIR" && pwd -P)"
  if [[ "$skills_real" != "$agents_real" ]]; then
    return
  fi

  local tmp_dir
  tmp_dir="$(mktemp -d "${SKILLS_TARGET_DIR}.tmp.XXXXXX")"
  cp -a "$SKILLS_TARGET_DIR/." "$tmp_dir/"
  rm "$SKILLS_TARGET_DIR"
  mv "$tmp_dir" "$SKILLS_TARGET_DIR"
  log "Materialized $SKILLS_TARGET_DIR as canonical skills directory before .agents compatibility sync"
}

sync_agents_skill_link() {
  local name="$1"
  local source="$SKILLS_TARGET_DIR/$name"
  local dest="$AGENTS_SKILLS_DIR/$name"

  if [[ "$DRY_RUN" == "true" ]]; then
    log "DRY RUN: would link $dest -> $source"
    return
  fi

  [[ -e "$source" || -L "$source" ]] || die "missing installed skill/module for compatibility link: $name"
  rm -rf "$dest"
  ln -s "$source" "$dest"
  log "$name linked into $AGENTS_SKILLS_DIR"
}

sync_agents_skill_entries() {
  if [[ "$DRY_RUN" == "true" ]]; then
    log "DRY RUN: would synchronize research-loop entries in $AGENTS_SKILLS_DIR"
    for skill in "${SKILLS[@]}"; do
      sync_agents_skill_link "$skill"
    done
    for module in "${INTERNAL_COMPILER_MODULES[@]}"; do
      sync_agents_skill_link "$module"
    done
    for retired_skill in "${RETIRED_SKILL_ENTRIES[@]}"; do
      remove_managed_skill_path "$AGENTS_SKILLS_DIR" "$retired_skill"
    done
    return
  fi

  run_mkdir "$AGENTS_SKILLS_DIR"
  AGENTS_SKILLS_DIR="$(cd "$AGENTS_SKILLS_DIR" && pwd)"
  if same_physical_dir "$AGENTS_SKILLS_DIR" "$SKILLS_TARGET_DIR"; then
    log "Agent skill compatibility path already resolves to skills target"
    return
  fi

  for skill in "${SKILLS[@]}"; do
    sync_agents_skill_link "$skill"
  done
  for module in "${INTERNAL_COMPILER_MODULES[@]}"; do
    sync_agents_skill_link "$module"
  done
  for retired_skill in "${RETIRED_SKILL_ENTRIES[@]}"; do
    remove_managed_skill_path "$AGENTS_SKILLS_DIR" "$retired_skill"
  done
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
  materialize_skills_target_if_agents_backed
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
  log "Installed internal compiler modules:"
  for module in "${INTERNAL_COMPILER_MODULES[@]}"; do
    copy_internal_module "$module"
  done
  for retired_skill in "${RETIRED_SKILL_ENTRIES[@]}"; do
    remove_retired_skill_entry "$retired_skill"
  done
  sync_agents_skill_entries
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
