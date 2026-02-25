#!/bin/bash
# Convenience script to update email from headers
# 更新邮件发件人信息的便捷脚本

set -e

echo "=========================================="
echo "Update Email From Headers"
echo "=========================================="
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose not found"
    echo "Please install docker-compose or run the command manually"
    exit 1
fi

# Check if django container is running
if ! docker-compose ps django | grep -q "Up"; then
    echo "Error: Django container is not running"
    echo "Please start the containers first: docker-compose up -d"
    exit 1
fi

# Parse arguments
DRY_RUN=""
BATCH_SIZE="100"
LIMIT=""
VERBOSITY="1"

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --limit)
            LIMIT="--limit $2"
            shift 2
            ;;
        -v|--verbosity)
            VERBOSITY="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run           Preview changes without updating database"
            echo "  --batch-size N      Process N records per batch (default: 100)"
            echo "  --limit N           Limit to N total messages"
            echo "  -v, --verbosity N   Set verbosity level (0-3, default: 1)"
            echo "  -h, --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --dry-run                    # Preview changes"
            echo "  $0                              # Update all emails"
            echo "  $0 --batch-size 500             # Use larger batches"
            echo "  $0 --dry-run --limit 10 -v 2    # Test with 10 emails, verbose"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build command
CMD="python manage.py update_email_from_headers"

if [ -n "$DRY_RUN" ]; then
    CMD="$CMD $DRY_RUN"
    echo "Running in DRY RUN mode - no changes will be saved"
    echo ""
fi

CMD="$CMD --batch-size $BATCH_SIZE"

if [ -n "$LIMIT" ]; then
    CMD="$CMD $LIMIT"
fi

CMD="$CMD -v $VERBOSITY"

echo "Executing: docker-compose exec django $CMD"
echo ""

# Execute
docker-compose exec django $CMD

echo ""
echo "Done!"
