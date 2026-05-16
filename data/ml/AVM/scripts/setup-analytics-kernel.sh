#!/bin/bash

cd /workspace/backend/analytics-service

uv sync

uv run python -m ipykernel install \
  --user \
  --name analytics \
  --display-name "analytics"