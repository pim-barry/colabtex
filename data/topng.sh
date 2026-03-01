#!/bin/bash

set -euo pipefail

echo "========== GeoTIFF -> PNG converter =========="

INPUT="${1:-}"
OUTPUT="${2:-}"
TMP_COLOR_TXT="tmp_colormap.txt"
TMP_COLOR_TIF="tmp_colored.tif"

if [ -z "$INPUT" ] || [ -z "$OUTPUT" ]; then
  echo "[ERROR] Usage: $0 input.tif output.png"
  exit 1
fi

if [ ! -f "$INPUT" ]; then
  echo "[ERROR] Input file does not exist: $INPUT"
  exit 1
fi

if ! command -v gdal_translate >/dev/null 2>&1; then
  echo "[ERROR] Missing tool: gdal_translate"
  echo "        Install GDAL (e.g. brew install gdal)"
  exit 1
fi

echo "[DEBUG] Input:  $INPUT"
echo "[DEBUG] Output: $OUTPUT"

rm -f "$OUTPUT" "$TMP_COLOR_TXT" "$TMP_COLOR_TIF"

# Try a class-color rendering first (good for lc_*.tif with values 0..9)
if command -v gdaldem >/dev/null 2>&1; then
  cat > "$TMP_COLOR_TXT" <<'EOF'
0 210 0 0
1 253 211 39
2 35 152 0
3 8 94 0
4 249 150 39
5 141 139 0
6 149 109 255
7 149 109 196
8 154 154 154
9 20 69 249
nv 0 0 0 0
EOF

  echo "[DEBUG] Trying colored PNG via gdaldem color-relief..."
  if gdaldem color-relief "$INPUT" "$TMP_COLOR_TXT" "$TMP_COLOR_TIF" -alpha >/dev/null 2>&1; then
    gdal_translate -of PNG "$TMP_COLOR_TIF" "$OUTPUT" >/dev/null
    echo "[OK] Wrote colored PNG: $OUTPUT"
  else
    echo "[WARN] gdaldem color-relief failed; falling back to grayscale PNG"
    gdal_translate -of PNG "$INPUT" "$OUTPUT" >/dev/null
    echo "[OK] Wrote grayscale PNG: $OUTPUT"
  fi
else
  echo "[WARN] gdaldem not found; writing grayscale PNG"
  gdal_translate -of PNG "$INPUT" "$OUTPUT" >/dev/null
  echo "[OK] Wrote grayscale PNG: $OUTPUT"
fi

rm -f "$TMP_COLOR_TXT" "$TMP_COLOR_TIF"
echo "========== DONE =========="
