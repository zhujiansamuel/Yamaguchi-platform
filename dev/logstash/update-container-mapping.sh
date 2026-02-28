#!/bin/bash
# Script to generate container ID to name mapping for Logstash translate filter
# Run this script on the host machine

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAPPING_FILE="$SCRIPT_DIR/data/container-mapping.yml"

echo "Generating container mapping..."

# Generate YAML mapping
echo "# Container ID to Name Mapping" > "$MAPPING_FILE"
echo "# Auto-generated at $(date)" >> "$MAPPING_FILE"
echo "" >> "$MAPPING_FILE"

# Get all running containers and create mapping (short ID -> name)
docker ps --format "{{.ID}} {{.Names}}" | while read -r id name; do
  echo "\"$id\": \"$name\"" >> "$MAPPING_FILE"
done

echo "Container mapping updated: $MAPPING_FILE"
echo "Total containers mapped: $(docker ps -q | wc -l)"
