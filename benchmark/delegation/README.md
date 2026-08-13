# DelegationBench — pilot harness
设计: ../../docs/delegation-bench-design-v0.1.md
用法: ./run_one.sh <t2|t4> <A|B> <run_id> <seed>   # 结果追加 RESULTS.jsonl
T4 施加 S1(随机时点 SIGKILL agent + 复活session);T2 内置 S3+S4(故障+注入)。
评分全确定性: score/score_t2.py score/score_t4.py。凭证按 run 注入、run 毕即删。
