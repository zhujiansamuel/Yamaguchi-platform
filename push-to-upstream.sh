#!/usr/bin/env bash
# 将本仓库中 subtree 子目录的修改推送到对应的原仓库
# 用法: ./push-to-upstream.sh [子目录名]
#       不指定子目录则推送全部

set -e
cd "$(dirname "$0")"
CONFIG="${CONFIG:-subtrees.config}"
DEFAULT_BRANCH="${SUBTREE_BRANCH:-main}"

# Workaround: git 2.39+ 的 git-subtree 中 `dirname "$prefix/."` 对单层目录
# 会返回 "." 而非目录名本身，导致 "assertion failed: test README.md = ."
# 检测到此 bug 时，自动使用修复版脚本。
_SUBTREE_FIX_DIR=/tmp/git-subtree-fix-$$
_setup_subtree_fix() {
  local orig
  orig="$(git --exec-path)/git-subtree"
  if bash -c 'test "$(dirname "probe/.")" = "probe"' 2>/dev/null; then
    return  # dirname 行为正常，无需修复
  fi
  mkdir -p "$_SUBTREE_FIX_DIR"
  cp "$orig" "$_SUBTREE_FIX_DIR/git-subtree"
  sed -i 's|dir="$(dirname "$arg_prefix/.")".*|dir="${arg_prefix%/}"|' \
    "$_SUBTREE_FIX_DIR/git-subtree"
  ln -sf "$(git --exec-path)/git-sh-setup"  "$_SUBTREE_FIX_DIR/git-sh-setup"
  ln -sf "$(git --exec-path)/git-sh-i18n"   "$_SUBTREE_FIX_DIR/git-sh-i18n" 2>/dev/null || true
  export GIT_EXEC_PATH="$_SUBTREE_FIX_DIR"
  export PATH="$_SUBTREE_FIX_DIR:$PATH"
  echo "  [注意] 已启用 git-subtree 补丁（git dirname bug）"
}
_setup_subtree_fix
trap 'rm -rf "$_SUBTREE_FIX_DIR"' EXIT

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
