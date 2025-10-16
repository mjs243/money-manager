@echo off
REM git_init.bat - initialize github repo

set REPO_NAME=budget-analyzer
set USERNAME=mjs243

git init
git config user.name %USERNAME%
git config user.email "malikjsnowden@gmail.com"

REM create .gitignore
(
    echo venv/
    echo __pycache__/
    echo *.pyc
    echo .DS_Store
    echo data/transactions.csv
    echo data/output/*
    echo !data/output/.gitkeep
    echo logs/
    echo .env
    echo .idea/
) > .gitignore

type nul > data\output\.gitkeep
type nul > logs\.gitkeep

git add .
git commit -m "initial commit: project scaffold"

echo ✅ git initialized
echo next: create repo on github (%REPO_NAME%) then:
echo   git remote add origin https://github.com/%USERNAME%/%REPO_NAME%.git
echo   git branch -M main
echo   git push -u origin main