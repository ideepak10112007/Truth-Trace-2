#!/usr/bin/env bash
cd "$(dirname "$0")/backend"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
python -m app.data.seed
uvicorn app.main:app --reload
