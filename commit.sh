#!/bin/sh
set -e

if test -z "$(git status -s)"; then
  echo 'no commit'
  exit 0;
else
  git config --local user.email "1982989137@qq.com"
  git config --local user.name "flow2000"
  git pull origin master
  git add data/*
  git commit -m "update bing json"
fi