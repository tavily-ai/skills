#!/usr/bin/env bash
# Copy the repo's skills and license into the package before testing or publishing.
# Skills are nested by category (skills/<category>/<name>/); the package ships them flat.
set -euo pipefail
cd "$(dirname "$0")"
rm -rf skills
mkdir skills
for dir in ../skills/*/*/; do
  cp -R "${dir%/}" skills/
done
cp ../LICENSE LICENSE
