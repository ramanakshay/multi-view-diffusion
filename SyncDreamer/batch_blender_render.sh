#!/usr/bin/env bash
# batch_blender_render.sh
# Usage: ./batch_blender_render.sh <input_root_dir> <output_root_dir> <camera_type>
# Scans input_root_dir (including subdirectories) for .glb files, renders each using Blender CLI,
# and outputs into <output_root_dir>/<model_id>/. Saves list of model IDs to a text file.

set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 <input_root_dir> <output_root_dir> <camera_type>"
  exit 1
fi

INPUT_ROOT="$1"
OUTPUT_ROOT="$2"
CAM_TYPE="$3"

# Verify Blender script exists
BLENDER_SCRIPT="blender_script.py"
if [[ ! -f "$BLENDER_SCRIPT" ]]; then
  echo "Error: $BLENDER_SCRIPT not found in $(pwd)"
  exit 1
fi

# Array to collect model IDs
declare -a MODEL_IDS=()

echo "Scanning for .glb files under $INPUT_ROOT..."
find "$INPUT_ROOT" -type f -name '*.glb' | while IFS= read -r GLB_PATH; do
  # Extract base filename without extension (model ID)
  MODEL_ID=$(basename "$GLB_PATH" .glb)
  MODEL_IDS+=("$MODEL_ID")

  OUTPUT_DIR="$OUTPUT_ROOT/$MODEL_ID"
  echo "Rendering $GLB_PATH -> $OUTPUT_DIR"
  mkdir -p "$OUTPUT_DIR"

  blender-3.3.2-linux-x64/blender --background --python "$BLENDER_SCRIPT" -- \
    --object_path "$GLB_PATH" \
    --output_dir "$OUTPUT_DIR" \
    --camera_type "$CAM_TYPE"

done

# After all rendering is complete, restructure and move PNGs
echo "Reorganizing PNGs and collecting folder names..."

> "$OUTPUT_ROOT/model_folders.txt"  # Clear or create log file

find "$OUTPUT_ROOT" -mindepth 1 -maxdepth 1 -type d | while IFS= read -r MODEL_OUT_DIR; do
    # Find deepest folder containing PNGs (assuming only one such leaf per model)
    PNG_DIR=$(find "$MODEL_OUT_DIR" -type f -name '*.png' -exec dirname {} \; | sort -u | head -n 1)

    if [[ -n "$PNG_DIR" ]]; then
        FOLDER_NAME=$(basename "$PNG_DIR")  # e.g., 'a'
        TARGET_DIR="$OUTPUT_ROOT/$FOLDER_NAME"
        mkdir -p "$TARGET_DIR"

        # Move all PNG files
        find "$PNG_DIR" -maxdepth 1 -name '*.png' -exec mv -t "$TARGET_DIR" {} +
        
        # Move PKL file if exists
        find "$PNG_DIR" -maxdepth 1 -name '*.pkl' -exec mv -t "$TARGET_DIR" {} +
        
        # Cleanup: Remove source directory if empty
        if [ -d "$PNG_DIR" ]; then
            rmdir --ignore-fail-on-non-empty "$PNG_DIR"
        fi

        # Log folder name (only if not already logged)
        grep -qxF "$FOLDER_NAME" "$OUTPUT_ROOT/model_folders.txt" || echo "$FOLDER_NAME" >> "$OUTPUT_ROOT/model_folders.txt"
    fi
done
