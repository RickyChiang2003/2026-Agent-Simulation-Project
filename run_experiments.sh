#!/usr/bin/env bash
set -euo pipefail

printf "\n=== Medical Simulation Runner ===\n"
printf "組合編號對照：\n"
printf " 1) Control, R=5, V=0\n"
printf " 2) Control, R=5, V=1\n"
printf " 3) Control, R=10, V=0\n"
printf " 4) Control, R=10, V=1\n"
printf " 5) Experimental, R=5, V=0\n"
printf " 6) Experimental, R=5, V=1\n"
printf " 7) Experimental, R=10, V=0\n"
printf " 8) Experimental, R=10, V=1\n\n"

read -r -p "每組要跑幾次 trial? (預設 1): " trials
trials=${trials:-1}

if ! [[ "$trials" =~ ^[0-9]+$ ]] || [ "$trials" -lt 1 ]; then
  echo "錯誤：trial 必須是 >= 1 的整數"
  exit 1
fi

read -r -p "要跑哪些組合? 輸入 all 或逗號編號（例: 1,2,5）: " configs
configs=${configs:-all}

if [ "$configs" = "all" ] || [ "$configs" = "ALL" ]; then
  echo "開始執行：python3 main.py --trials $trials --configs all"
  python3 main.py --trials "$trials" --configs all
  exit 0
fi

# 驗證格式與範圍
tmp=$(echo "$configs" | tr ',' ' ')
validated=()
for x in $tmp; do
  x=$(echo "$x" | xargs)
  if ! [[ "$x" =~ ^[0-9]+$ ]]; then
    echo "錯誤：組合編號必須是數字（1~8）"
    exit 1
  fi
  if [ "$x" -lt 1 ] || [ "$x" -gt 8 ]; then
    echo "錯誤：組合編號超出範圍（1~8）"
    exit 1
  fi
  validated+=("$x")
done

configs_csv=$(IFS=,; echo "${validated[*]}")
echo "開始執行：python3 main.py --trials $trials --configs $configs_csv"
python3 main.py --trials "$trials" --configs "$configs_csv"
