#!/bin/bash

# ============================================================================
# Generate Mock Data for Data Aggregation App
# ============================================================================
# This script generates random test data for all models in data_aggregation app
# ============================================================================

set -e  # Exit on error

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}  Generate Mock Data for Data Aggregation App${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Default values
COUNT=10
CLEAR=false
DOCKER=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--count)
            COUNT="$2"
            shift 2
            ;;
        --clear)
            CLEAR=true
            shift
            ;;
        --docker)
            DOCKER=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -c, --count NUM    Number of records to create for each model (default: 10)"
            echo "  --clear            Clear existing data before generating new data"
            echo "  --docker           Run inside Docker container (use 'docker compose exec')"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --count 20                    # Generate 20 records per model"
            echo "  $0 --clear --count 50            # Clear and generate 50 records"
            echo "  $0 --docker --count 30           # Run in Docker with 30 records"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Run '$0 --help' for usage information"
            exit 1
            ;;
    esac
done

# Build the command
CMD="python manage.py generate_test_data --count $COUNT"
if [ "$CLEAR" = true ]; then
    CMD="$CMD --clear"
    echo -e "${YELLOW}⚠️  WARNING: This will clear all existing data!${NC}"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo -e "${YELLOW}Cancelled.${NC}"
        exit 0
    fi
fi

# Execute the command
echo -e "${GREEN}🚀 Starting data generation...${NC}"
echo -e "${BLUE}   Count: ${COUNT} records per model${NC}"
echo -e "${BLUE}   Clear existing: ${CLEAR}${NC}"
echo ""

if [ "$DOCKER" = true ]; then
    echo -e "${GREEN}Running in Docker container...${NC}"
    docker compose exec django $CMD
else
    echo -e "${GREEN}Running locally...${NC}"
    $CMD
fi

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}============================================================================${NC}"
    echo -e "${GREEN}✅ Mock data generation completed successfully!${NC}"
    echo -e "${GREEN}============================================================================${NC}"
    echo ""
    echo -e "${BLUE}📊 Data Summary:${NC}"
    if [ "$DOCKER" = true ]; then
        docker compose exec django python manage.py shell -c "
from apps.data_aggregation.models import *
models_info = [
    ('AggregationSource', AggregationSource.objects.count()),
    ('AggregatedData', AggregatedData.objects.count()),
    ('AggregationTask', AggregationTask.objects.count()),
    ('iPhone', iPhone.objects.count()),
    ('iPad', iPad.objects.count()),
    ('TemporaryChannel', TemporaryChannel.objects.count()),
    ('LegalPersonOffline', LegalPersonOffline.objects.count()),
    ('EcSite', EcSite.objects.count()),
    ('OfficialAccount', OfficialAccount.objects.count()),
    ('Purchasing', Purchasing.objects.count()),
    ('GiftCard', GiftCard.objects.count()),
    ('DebitCard', DebitCard.objects.count()),
    ('CreditCard', CreditCard.objects.count()),
    ('DebitCardPayment', DebitCardPayment.objects.count()),
    ('CreditCardPayment', CreditCardPayment.objects.count()),
    ('Inventory', Inventory.objects.count()),
]
for name, count in models_info:
    print(f'  {name}: {count} records')
"
    else
        python manage.py shell -c "
from apps.data_aggregation.models import *
models_info = [
    ('AggregationSource', AggregationSource.objects.count()),
    ('AggregatedData', AggregatedData.objects.count()),
    ('AggregationTask', AggregationTask.objects.count()),
    ('iPhone', iPhone.objects.count()),
    ('iPad', iPad.objects.count()),
    ('TemporaryChannel', TemporaryChannel.objects.count()),
    ('LegalPersonOffline', LegalPersonOffline.objects.count()),
    ('EcSite', EcSite.objects.count()),
    ('OfficialAccount', OfficialAccount.objects.count()),
    ('Purchasing', Purchasing.objects.count()),
    ('GiftCard', GiftCard.objects.count()),
    ('DebitCard', DebitCard.objects.count()),
    ('CreditCard', CreditCard.objects.count()),
    ('DebitCardPayment', DebitCardPayment.objects.count()),
    ('CreditCardPayment', CreditCardPayment.objects.count()),
    ('Inventory', Inventory.objects.count()),
]
for name, count in models_info:
    print(f'  {name}: {count} records')
"
    fi
    echo ""
    echo -e "${BLUE}🌐 You can now access:${NC}"
    echo -e "${BLUE}  - Django Admin: https://data.yamaguchi.lan/admin/${NC}"
    echo -e "${BLUE}  - API: https://data.yamaguchi.lan/api/${NC}"
else
    echo ""
    echo -e "${RED}❌ Mock data generation failed!${NC}"
    echo -e "${RED}Please check the error messages above.${NC}"
    exit 1
fi
