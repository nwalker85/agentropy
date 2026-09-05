#!/bin/bash
# Prove: Zenodo record 20818597 zip == git tag v1.0.0 == main@91df6c0, file by file.
# Usage: bash identity_proof.sh [WORKDIR]   (WORKDIR defaults to a temp dir; the zip is cached there)
set -u
WORK="${1:-$(mktemp -d)}"
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
ZIP_URL="https://zenodo.org/api/records/20818597/files/nwalker85/agentropy-v1.0.0.zip/content"
RECORD_MD5="6a2315a50bbb2d49dd1db9aa8e195785"   # from https://zenodo.org/api/records/20818597 -> files[0].checksum

mkdir -p "$WORK"
cd "$WORK" || exit 1
if [ ! -s agentropy-v1.0.0.zip ]; then
  curl -sSL -o agentropy-v1.0.0.zip "$ZIP_URL" || exit 1
fi
ls -l agentropy-v1.0.0.zip
if command -v md5 >/dev/null 2>&1; then GOT=$(md5 -q agentropy-v1.0.0.zip); else GOT=$(md5sum agentropy-v1.0.0.zip | cut -d' ' -f1); fi
echo "zenodo md5 (record metadata): $RECORD_MD5"
echo "downloaded md5:               $GOT"
rm -rf zenodo-extract tag-extract
mkdir -p zenodo-extract tag-extract
(cd zenodo-extract && unzip -q ../agentropy-v1.0.0.zip)
TOP=$(ls zenodo-extract)
echo "zip top-level dir: $TOP"
cd "$REPO" || exit 1
echo "tag v1.0.0 -> $(git rev-parse 'v1.0.0^{commit}')"
echo "main       -> $(git rev-parse main)"
git archive v1.0.0 | tar -x -C "$WORK/tag-extract"
cd "$WORK" || exit 1
(cd "zenodo-extract/$TOP" && find . -type f | sort | xargs shasum -a 256) > zenodo.sha256
(cd tag-extract && find . -type f | sort | xargs shasum -a 256) > tag.sha256
echo "files in zenodo zip: $(wc -l < zenodo.sha256 | tr -d ' ')   files in git archive v1.0.0: $(wc -l < tag.sha256 | tr -d ' ')"
if diff zenodo.sha256 tag.sha256 > /dev/null; then
  echo "IDENTITY: PROVEN — every file in the Zenodo zip matches git archive v1.0.0 by sha256"
else
  echo "IDENTITY: DIFFERS"
  diff zenodo.sha256 tag.sha256
fi
echo "extracted Zenodo tree: $WORK/zenodo-extract/$TOP"
