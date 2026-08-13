#!/usr/bin/env bash
# run_one.sh <t2|t4> <A|B> <run_id> <seed> — 单 run 驱动器(pilot)
# T4: 主session 后台起 → seeded 时点 SIGKILL 整进程组(S1) → 20s 后复活session → 评分
# T2: 单 fg session → 评分。凭证 run 内注入、退出时删除(trap)。
set -uo pipefail
BD="$(cd "$(dirname "$0")" && pwd)"
TASK="$1"; ARM="$2"; RID="$3"; SEED="${4:-1}"
RUN="$BD/runs/$RID"; WS="$RUN/work"; HM="$RUN/home"
mkdir -p "$WS" "$HM/.claude"
trap 'rm -f "$HM/.claude/.credentials.json"' EXIT
cp ~/.claude/.credentials.json "$HM/.claude/"
printf '{"hasCompletedOnboarding": true}\n' > "$HM/.claude.json"
bash "$BD/tasks/build_$TASK.sh" "$WS" "$SEED" > "$RUN/build.log" 2>&1
if [ "$ARM" = "B" ]; then
  mkdir -p "$WS/specs"
  cp ~/STL/semantic-tension-language/spec/intent-contract-spec-v0.1-draft.md \
     ~/STL/semantic-tension-language/spec/board-as-spec-protocol-v0.1-draft.md \
     ~/STL/semantic-tension-language/spec/eval-verdict-vocabulary-v0.1-draft.md "$WS/specs/"
fi
PROMPT="$BD/prompts/arm$ARM.txt"
cd "$WS"
if [ "$TASK" = "t4" ]; then
  KILL_AT=$(( 70 + (SEED * 13) % 40 ))          # 主session存活 70-109s(死亡窗口内)
  setsid bash -c "HOME='$HM' claude -p --dangerously-skip-permissions < '$PROMPT' > '$RUN/out_main.txt' 2>'$RUN/err_main.txt'" &
  SPID=$!
  sleep "$KILL_AT"
  kill -9 -- "-$(ps -o pgid= "$SPID" 2>/dev/null | tr -d ' ')" 2>/dev/null || kill -9 "$SPID" 2>/dev/null
  echo "killed main session at +${KILL_AT}s" > "$RUN/stressor.log"
  sleep 20
  HOME="$HM" timeout 420 claude -p --dangerously-skip-permissions < "$BD/prompts/revive.txt" > "$RUN/out_revive.txt" 2>"$RUN/err_revive.txt"
  echo "revive exit=$?" >> "$RUN/stressor.log"
else
  HOME="$HM" timeout 420 claude -p --dangerously-skip-permissions < "$PROMPT" > "$RUN/out_main.txt" 2>"$RUN/err_main.txt"
  echo "main exit=$?" > "$RUN/stressor.log"
fi
SCORE=$(python3 "$BD/score/score_$TASK.py" "$WS")
echo "{\"run\":\"$RID\",\"task\":\"$TASK\",\"arm\":\"$ARM\",\"seed\":$SEED,\"score\":$SCORE}" >> "$BD/RESULTS.jsonl"
echo "== $RID ($TASK/$ARM/seed$SEED) =="; echo "$SCORE"
