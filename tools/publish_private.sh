#!/bin/bash
# Minimal private publish script for EventFlow Pro packages
set -e

PACKAGE_DIR=$1
if [ -z "$PACKAGE_DIR" ]; then
  echo "Usage: $0 <package_directory>"
  exit 1
fi

if [ -z "$PRIVATE_PYPI_URL" ]; then
  echo "error: PRIVATE_PYPI_URL environment variable not set"
  exit 1
fi

cd "$PACKAGE_DIR"
rm -rf dist/
python3 -m build
# In a real impl, use twine to upload to private index
# twine upload --repository-url "$PRIVATE_PYPI_URL" dist/*
echo "SUCCESS: Published $PACKAGE_DIR to $PRIVATE_PYPI_URL (stub)"
