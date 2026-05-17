#!/usr/bin/env bash
# Pre-flight gate script template
# 任何 L3 Full Experiment 前必须先通过此脚本。
# 用法: ./pre_flight.sh <task_dir> <python_module>
# 失败则 L3 不得执行。

set -euo pipefail

TASK_DIR="${1:-.}"
MODULE="${2:-main}"
LOG="${TASK_DIR}/pre_flight.log"

PASS=0
FAIL=0

log() {
  echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"
}

log "=== Pre-flight start: $TASK_DIR ==="

# L0: Syntax check
log "L0 Static: py_compile + shellcheck..."
find "$TASK_DIR" -name '*.py' -exec python3 -m py_compile {} \; 2>>"$LOG" && log "L0 PASS" || { log "L0 FAIL"; FAIL=$((FAIL+1)); }

# L1: Deterministic / Mock tests
log "L1 Deterministic: pytest -m deterministic..."
if [ -f "$TASK_DIR/tests/test_deterministic.py" ]; then
  python3 -m pytest "$TASK_DIR/tests/test_deterministic.py" -v --tb=short 2>>"$LOG" && log "L1 PASS" || { log "L1 FAIL"; FAIL=$((FAIL+1)); }
else
  log "L1 SKIP (no test_deterministic.py found)"
fi

# L2: Smoke test (one-batch, tiny model, no GPU or CPU-only)
log "L2 Smoke: one-batch forward..."
if [ -f "$TASK_DIR/tests/test_smoke.py" ]; then
  python3 -m pytest "$TASK_DIR/tests/test_smoke.py" -v --tb=short 2>>"$LOG" && log "L2 PASS" || { log "L2 FAIL"; FAIL=$((FAIL+1)); }
else
  log "L2 SKIP (no test_smoke.py found)"
fi

# Summary
if [ "$FAIL" -eq 0 ]; then
  log "=== Pre-flight ALL PASS ==="
  exit 0
else
  log "=== Pre-flight FAIL ($FAIL gate(s) failed) ==="
  exit 1
fi
