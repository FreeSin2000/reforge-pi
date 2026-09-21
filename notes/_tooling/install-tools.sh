#!/usr/bin/env bash
#
# 安装源码阅读 / 内核调试所需工具。
# 需要 root：  sudo bash notes/_tooling/install-tools.sh
#
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "请用 sudo 运行： sudo bash $0" >&2
  exit 1
fi

PKGS=(
  cscope          # 符号索引：找调用者 / 被调用者
  universal-ctags # tags 生成
  clangd          # 语义跳转（LSP）
  bear            # 生成 compile_commands.json
  dwarves         # pahole：结构体内存布局 / BTF
)

echo "[1/2] apt-get update"
apt-get update

echo "[2/2] 安装： ${PKGS[*]}"
apt-get install -y "${PKGS[@]}"

echo
echo "完成，验证："
for t in cscope ctags clangd bear pahole; do
  printf "  %-10s" "$t"
  if command -v "$t" >/dev/null 2>&1; then
    echo "OK  ($(command -v "$t"))"
  else
    echo "缺失"
  fi
done
