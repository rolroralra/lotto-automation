#!/bin/bash
# Lambda Deployment Package Builder
# Creates a ZIP file with dependencies for Lambda deployment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${SCRIPT_DIR}/src"
BUILD_DIR="${SCRIPT_DIR}/build"
OUTPUT_FILE="${SCRIPT_DIR}/deployment.zip"

echo "=== Building Lambda Deployment Package ==="
echo "Source: ${SRC_DIR}"
echo "Output: ${OUTPUT_FILE}"
echo ""

# Clean previous build
rm -rf "${BUILD_DIR}"
rm -f "${OUTPUT_FILE}"
mkdir -p "${BUILD_DIR}"

# Install dependencies for Lambda (Linux x86_64)
echo "Step 1: Installing dependencies..."
pip install \
    --target "${BUILD_DIR}" \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.9 \
    --only-binary=:all: \
    --upgrade \
    -r "${SCRIPT_DIR}/requirements.txt" \
    2>/dev/null || pip install --target "${BUILD_DIR}" -r "${SCRIPT_DIR}/requirements.txt"

# Copy source code
echo "Step 2: Copying source code..."
cp "${SRC_DIR}"/*.py "${BUILD_DIR}/"

# Create ZIP
echo "Step 3: Creating deployment package..."
cd "${BUILD_DIR}"
zip -r "${OUTPUT_FILE}" . -q

# Cleanup build directory
rm -rf "${BUILD_DIR}"

# Show result
SIZE=$(ls -lh "${OUTPUT_FILE}" | awk '{print $5}')
echo ""
echo "=== Build Complete ==="
echo "Package: ${OUTPUT_FILE}"
echo "Size: ${SIZE}"
