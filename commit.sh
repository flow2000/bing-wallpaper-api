#!/bin/sh
set -e

# 可选参数：地区（如 zh-CN）。传入时只提交该地区的 json，否则提交 data 目录全部变更
REGION="$1"
if [ -n "$REGION" ]; then
  PATTERN="data/${REGION}_all.json"
  MESSAGE="update bing json ${REGION}"
else
  PATTERN="data"
  MESSAGE="update bing json"
fi

if git diff --quiet -- $PATTERN; then
  echo 'no commit'
  exit 0
fi

git config --local user.email "1982989137@qq.com"
git config --local user.name "flow2000"

# 多个分地区工作流可能同时推送 master：先暂存本地变更，与远端 rebase 对齐后再恢复，避免 non-fast-forward
git stash push -m "bing-json-tmp" -- $PATTERN
git pull --rebase origin master
git stash pop

git add $PATTERN
git commit -m "$MESSAGE"
