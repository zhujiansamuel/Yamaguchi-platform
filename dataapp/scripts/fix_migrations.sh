#!/bin/bash
# Script to fix migration order inconsistency in data_acquisition app
#
# Problem: Database has 0003 applied but not 0002 (which we just created)
# Solution: Fake-apply 0002 since the HistoricalSyncLog table likely already exists

set -e

echo "================================================"
echo "Fixing data_acquisition migration inconsistency"
echo "================================================"
echo ""

echo "Step 1: Fake-apply 0002_historicalsynclog (table likely already exists)"
python manage.py migrate data_acquisition 0002_historicalsynclog --fake

echo ""
echo "Step 2: Apply all remaining migrations normally"
python manage.py migrate data_acquisition

echo ""
echo "Step 3: Apply data_aggregation migrations"
python manage.py migrate data_aggregation

echo ""
echo "================================================"
echo "Migration fix complete!"
echo "================================================"
echo ""
echo "Verifying migration status:"
python manage.py showmigrations data_acquisition data_aggregation
