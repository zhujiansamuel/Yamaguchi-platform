-- SQL script to fix migration inconsistency in django_migrations table
-- This manually inserts the missing 0002_historicalsynclog migration record
-- Run this directly in PostgreSQL before starting Django

-- First, check what migrations are currently recorded for data_acquisition
SELECT id, app, name, applied
FROM django_migrations
WHERE app = 'data_acquisition'
ORDER BY id;

-- Insert the missing 0002_historicalsynclog migration
-- This will mark it as applied so Django doesn't complain about inconsistent history
INSERT INTO django_migrations (app, name, applied)
VALUES ('data_acquisition', '0002_historicalsynclog', NOW())
ON CONFLICT DO NOTHING;

-- Verify the fix
SELECT id, app, name, applied
FROM django_migrations
WHERE app = 'data_acquisition'
ORDER BY id;

-- Expected result after fix:
-- data_acquisition.0001_initial
-- data_acquisition.0002_historicalsynclog (newly inserted)
-- data_acquisition.0003_alter_historicalsynclog_operation_type_and_more (already exists)
-- Ready for 0004_trackingbatch_trackingjob to be applied by Django
