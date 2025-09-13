#!/usr/bin/env bash
set -euo pipefail

# Path to your existing script
CLOUD_AGE="${HOME}/Desktop/cloud-age.sh"

# Ensure operation and path are provided
if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <e|d> <path>"
  exit 1
fi

op="$1"
root="$2"

# Check operation
if [[ "$op" != "e" && "$op" != "d" ]]; then
  echo "Operation must be 'e' (encrypt) or 'd' (decrypt)"
  exit 1
fi

# Ensure path exists
if [[ ! -d "$root" ]]; then
  echo "Path is not a directory: $root"
  exit 1
fi

# Iterate over all non-hidden entries in the directory
shopt -s nullglob
for item in "$root"/*; do
  echo "Processing: $item"
  "$CLOUD_AGE" "$op" "$item"
done
shopt -u nullglob
