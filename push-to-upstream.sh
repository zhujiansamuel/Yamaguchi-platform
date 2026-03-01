#!/usr/bin/env bash
# 将本仓库中 subtree 子目录的修改推送到对应的原仓库
# 用法: ./push-to-upstream.sh [子目录名]
#       不指定子目录则推送全部

set -e
cd "$(dirname "$0")"
CONFIG="${CONFIG:-subtrees.config}"
DEFAULT_BRANCH="${SUBTREE_BRANCH:-main}"

ensure_remote() {
  local name="$1"
  local url="$2"
  if ! git remote get-url "$name" &>/dev/null; then
    git remote add "$name" "$url"
    echo "  + 已添加 remote: $name"
  fi
}

push_one() {
  local dir="$1"
  local url="$2"
  local branch="${3:-$DEFAULT_BRANCH}"
  local remote="$dir"
  ensure_remote "$remote" "$url"
  echo ">>> 推送 $dir -> $url (branch: $branch)"
  git subtree push --prefix="$dir" "$remote" "$branch"
}

push_all() {
  while IFS='|' read -r dir url branch; do
    [[ "$dir" =~ ^#.*$ || -z "$dir" ]] && continue
    push_one "$dir" "$url" "$branch"
  done < "$CONFIG"
}

if [[ -n "$1" ]]; then
  while IFS='|' read -r dir url branch; do
    [[ "$dir" =~ ^#.*$ || -z "$dir" ]] && continue
    if [[ "$dir" == "$1" ]]; then
      push_one "$dir" "$url" "$branch"
      exit 0
    fi
  done < "$CONFIG"
  echo "错误: 未找到子目录 '$1'"
  exit 1
else
  push_all
fi
