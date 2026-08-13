#!/usr/bin/env bash
# batch_pilot.sh — pilot 8 run:t2/t4 × A/B × seeds 1,2。两条流并行,流内串行。
set -uo pipefail
BD="$(cd "$(dirname "$0")" && pwd)"
TS=$(date +%H%M)
( for arm in A B; do for s in 1 2; do
    "$BD/run_one.sh" t2 "$arm" "pilot-t2-$arm$s-$TS" "$s" >> "$BD/runs/batch-t2.log" 2>&1
    echo "DONE t2-$arm$s $(date +%T)" >> "$BD/runs/batch-t2.log"
  done; done ) &
P1=$!
( for arm in A B; do for s in 1 2; do
    "$BD/run_one.sh" t4 "$arm" "pilot-t4-$arm$s-$TS" "$s" >> "$BD/runs/batch-t4.log" 2>&1
    echo "DONE t4-$arm$s $(date +%T)" >> "$BD/runs/batch-t4.log"
  done; done ) &
P2=$!
wait $P1 $P2
echo "PILOT BATCH COMPLETE $(date +%T) — results:"
tail -8 "$BD/RESULTS.jsonl"
