#!/bin/bash
# Script to clean up old Elasticsearch indices
# Deletes docker-logs indices older than 30 days

ELASTICSEARCH_URL="http://localhost:9200"
DAYS_TO_KEEP=30
INDEX_PATTERN="docker-logs-*"

echo "Cleaning up indices older than $DAYS_TO_KEEP days..."

# Get current date in seconds
CURRENT_DATE=$(date +%s)

# Calculate cutoff date
CUTOFF_DATE=$(date -d "$DAYS_TO_KEEP days ago" +%Y.%m.%d)

echo "Cutoff date: $CUTOFF_DATE"

# Get all indices matching pattern
INDICES=$(curl -s "$ELASTICSEARCH_URL/_cat/indices/$INDEX_PATTERN?h=index" | sort)

for INDEX in $INDICES; do
  # Extract date from index name (docker-logs-YYYY.MM.DD)
  INDEX_DATE=$(echo $INDEX | grep -oP '\d{4}\.\d{2}\.\d{2}')

  if [ ! -z "$INDEX_DATE" ]; then
    # Compare dates
    if [[ "$INDEX_DATE" < "$CUTOFF_DATE" ]]; then
      echo "Deleting old index: $INDEX (date: $INDEX_DATE)"
      curl -X DELETE "$ELASTICSEARCH_URL/$INDEX?pretty" 2>/dev/null
    else
      echo "Keeping index: $INDEX (date: $INDEX_DATE)"
    fi
  fi
done

echo "Cleanup completed!"
