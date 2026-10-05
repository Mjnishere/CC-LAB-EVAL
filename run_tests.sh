#!/bin/bash
# Run from project root after containers are up

mkdir -p results

LEVELS=(1 2 4 8 16)

echo "==============================="
echo "  Festify k6 Load Tests"
echo "==============================="

for VUS in "${LEVELS[@]}"; do
    echo ""
    echo "--- VUs (concurrency): $VUS ---"
    k6 run \
      --env VUS=$VUS \
      --out csv=results/w${VUS}.csv \
      --summary-trend-stats="avg,p(95),max" \
      load_test.js
    echo "Results saved to results/w${VUS}.csv"
done
