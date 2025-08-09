@echo off
REM 建立資料夾
mkdir ".github\workflows" 2>nul

REM 建立並寫入 ci.yml
(
echo name: CI
echo.
echo on:
echo   push:
echo     branches: [ main ]
echo   pull_request:
echo     branches: [ main ]
echo.
echo jobs:
echo   build:
echo     runs-on: ubuntu-latest
echo     steps:
echo       - uses: actions/checkout@v4
echo       - uses: actions/setup-python@v5
echo         with:
echo           python-version: "3.11"
echo       - run: pip install -r requirements.txt
echo       - run: ruff check .
echo       - run: black --check .
echo       - run: pytest
) > ".github\workflows\ci.yml"

echo.
echo GitHub Actions CI workflow 已建立：.github\workflows\ci.yml
pause
