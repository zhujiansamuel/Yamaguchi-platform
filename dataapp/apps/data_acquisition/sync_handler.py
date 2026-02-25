"""
Sync handler for processing Excel data and syncing to database.
Handles create, update, delete operations with version conflict detection.
"""
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.apps import apps
from django.utils import timezone

from .models import NextcloudSyncState, SyncConflict, SyncLog
from .excel_parser import ExcelParser, ExcelParseError
from .excel_writer import ExcelGenerator
from .webdav_client import NextcloudWebDAVClient

logger = logging.getLogger(__name__)


class SyncHandler:
    """
    Handles synchronization of Excel data to Django models.
    """

    # Model name to app label mapping
    MODEL_APP_MAP = {
        'Purchasing': 'data_aggregation',
        'OfficialAccount': 'data_aggregation',
        'GiftCard': 'data_aggregation',
        'DebitCard': 'data_aggregation',
        'CreditCard': 'data_aggregation',
        'TemporaryChannel': 'data_aggregation',
    }

    def __init__(self, file_path: str, event_user: str = '', celery_task_id: str = ''):
        """
        Initialize sync handler.

        Args:
            file_path: Nextcloud file path
            event_user: Nextcloud user who triggered the event
            celery_task_id: Celery task ID for logging
        """
        self.file_path = file_path
        self.event_user = event_user
        self.celery_task_id = celery_task_id
        self.webdav_client = NextcloudWebDAVClient()

        # Statistics
        self.stats = {
            'created': 0,
            'updated': 0,
            'deleted': 0,
            'conflicts': 0,
            'errors': 0,
        }

        # Track records that need ID writeback
        self.new_records = []

    def _log(self, operation_type: str, message: str, sync_state=None, success=True, error_message='', details=None):
        """Create sync log entry."""
        SyncLog.objects.create(
            sync_state=sync_state,
            operation_type=operation_type,
            celery_task_id=self.celery_task_id,
            file_path=self.file_path,
            message=message,
            details=details or {},
            success=success,
            error_message=error_message,
        )

    def _get_model_name(self) -> Optional[str]:
        """
        Extract model name from file path.

        Example: /Data/Purchasing_abc123.xlsx -> Purchasing

        Returns:
            Model name or None if not found
        """
        import re
        # Extract filename from path
        filename = self.file_path.split('/')[-1]
        # Remove extension
        name_part = filename.replace('.xlsx', '').replace('.xls', '')
        # Extract model name before underscore
        match = re.match(r'^([A-Za-z]+)_', name_part)
        if match:
            return match.group(1)
        return None

    def _get_model_class(self, model_name: str):
        """
        Get Django model class by name.

        Args:
            model_name: Model name (e.g., 'Purchasing')

        Returns:
            Model class

        Raises:
            ValueError: If model not found
        """
        app_label = self.MODEL_APP_MAP.get(model_name)
        if not app_label:
            raise ValueError(f"Unsupported model: {model_name}")

        try:
            return apps.get_model(app_label, model_name)
        except LookupError:
            raise ValueError(f"Model {app_label}.{model_name} not found")

    def _map_excel_to_model_fields(self, excel_row: Dict[str, Any], model_name: str) -> Dict[str, Any]:
        """
        Map Excel row data to Django model fields.

        Args:
            excel_row: Parsed Excel row data
            model_name: Model name

        Returns:
            Dictionary of model field names and values
        """
        field_mapping = ExcelGenerator.get_field_mapping(model_name)

        # Reverse mapping: Excel column name -> Django field name
        reverse_mapping = {excel_name: django_name for django_name, excel_name in field_mapping.items()}

        model_data = {}
        for excel_col, value in excel_row.items():
            if excel_col in ['__id', '__version', '__op', '_row_num']:
                continue

            django_field = reverse_mapping.get(excel_col)
            if django_field:
                model_data[django_field] = value

        return model_data

    def _check_version_conflict(self, instance, excel_version: str) -> bool:
        """
        Check if version conflict exists.

        Args:
            instance: Django model instance
            excel_version: Version from Excel

        Returns:
            True if conflict exists, False otherwise
        """
        if not hasattr(instance, 'updated_at'):
            return False

        # Convert DB version to string for comparison
        db_version = instance.updated_at.isoformat() if instance.updated_at else ''

        # Compare versions (exact match or close enough)
        return db_version != excel_version

    def _handle_conflict(self, sync_state, model_name: str, record_id: Optional[int],
                        excel_version: str, excel_data: Dict, db_instance=None):
        """
        Record a version conflict.

        Args:
            sync_state: NextcloudSyncState instance
            model_name: Model name
            record_id: Record ID
            excel_version: Version from Excel
            excel_data: Data from Excel
            db_instance: Current database instance (if exists)
        """
        db_version = ''
        db_data = None

        if db_instance:
            db_version = db_instance.updated_at.isoformat() if hasattr(db_instance, 'updated_at') else ''
            # Serialize db instance to dict (simplified)
            db_data = {f.name: getattr(db_instance, f.name) for f in db_instance._meta.fields}

        conflict = SyncConflict.objects.create(
            sync_state=sync_state,
            conflict_type='version_mismatch',
            model_name=model_name,
            record_id=record_id,
            excel_version=excel_version,
            db_version=db_version,
            excel_data=excel_data,
            db_data=db_data,
            status='pending',
        )

        self.stats['conflicts'] += 1
        self._log(
            'conflict_detected',
            f"Version conflict for {model_name} #{record_id}",
            sync_state,
            success=True,
            details={'conflict_id': conflict.id}
        )

        logger.warning(
            f"Conflict detected: {model_name} #{record_id} "
            f"(Excel: {excel_version}, DB: {db_version})"
        )

    def _process_row(self, row_data: Dict[str, Any], model_class, sync_state) -> bool:
        """
        Process a single Excel row.

        Args:
            row_data: Parsed Excel row
            model_class: Django model class
            sync_state: NextcloudSyncState instance

        Returns:
            True if processed successfully, False otherwise
        """
        model_name = model_class.__name__
        record_id = row_data.get('__id')
        version = row_data.get('__version')
        operation = row_data.get('__op')
        row_num = row_data.get('_row_num', '?')

        try:
            # Map Excel data to model fields
            model_data = self._map_excel_to_model_fields(row_data, model_name)

            # Handle DELETE operation
            if operation == 'DELETE':
                if not record_id:
                    logger.warning(f"Row {row_num}: Cannot delete without __id")
                    return False

                try:
                    instance = model_class.objects.get(pk=record_id)
                    instance.delete()
                    self.stats['deleted'] += 1
                    self._log(
                        'record_deleted',
                        f"Deleted {model_name} #{record_id}",
                        sync_state,
                        details={'row_num': row_num}
                    )
                    logger.info(f"Deleted {model_name} #{record_id}")
                    return True
                except model_class.DoesNotExist:
                    logger.warning(f"Row {row_num}: {model_name} #{record_id} not found for deletion")
                    return False

            # Handle UPDATE operation
            elif record_id:
                try:
                    instance = model_class.objects.get(pk=record_id)

                    # Check version conflict
                    if self._check_version_conflict(instance, version):
                        self._handle_conflict(sync_state, model_name, record_id, version, row_data, instance)
                        return False

                    # Update fields
                    for field, value in model_data.items():
                        setattr(instance, field, value)

                    instance.save()
                    self.stats['updated'] += 1
                    self._log(
                        'record_updated',
                        f"Updated {model_name} #{record_id}",
                        sync_state,
                        details={'row_num': row_num}
                    )
                    logger.info(f"Updated {model_name} #{record_id}")
                    return True

                except model_class.DoesNotExist:
                    logger.warning(f"Row {row_num}: {model_name} #{record_id} not found, treating as new record")
                    # Fall through to CREATE

            # Handle CREATE operation (no __id or not found)
            instance = model_class(**model_data)
            instance.save()

            self.stats['created'] += 1
            self.new_records.append({
                'row_num': row_num,
                'id': instance.id,
                'data': model_data
            })
            self._log(
                'record_created',
                f"Created {model_name} #{instance.id}",
                sync_state,
                details={'row_num': row_num}
            )
            logger.info(f"Created {model_name} #{instance.id}")
            return True

        except Exception as e:
            self.stats['errors'] += 1
            self._log(
                'sync_failed',
                f"Error processing row {row_num}",
                sync_state,
                success=False,
                error_message=str(e),
                details={'row_data': row_data}
            )
            logger.error(f"Error processing row {row_num}: {e}", exc_info=True)
            return False

    def sync(self) -> Dict[str, Any]:
        """
        Execute synchronization.

        Returns:
            Dictionary with sync results

        Raises:
            Exception: If sync fails
        """
        start_time = timezone.now()

        try:
            # Step 1: Get file info and check etag
            self._log('sync_started', f"Starting sync for {self.file_path}")
            logger.info(f"Starting sync for {self.file_path}")

            file_info = self.webdav_client.get_file_info(self.file_path)
            if not file_info:
                raise Exception(f"File not found or inaccessible: {self.file_path}")

            current_etag = file_info['etag']
            current_modified = file_info['modified']

            # Step 2: Get or create sync state
            model_name = self._get_model_name()
            if not model_name:
                raise Exception(f"Cannot extract model name from file path: {self.file_path}")

            sync_state, created = NextcloudSyncState.objects.get_or_create(
                file_path=self.file_path,
                defaults={
                    'model_name': model_name,
                    'last_etag': '',
                }
            )

            # Step 3: Check if already processed (idempotency)
            if sync_state.last_etag == current_etag:
                logger.info(f"ETag {current_etag} already processed, skipping (idempotent)")
                self._log(
                    'sync_completed',
                    f"Sync skipped (duplicate etag)",
                    sync_state,
                    details={'etag': current_etag}
                )
                return {
                    'status': 'skipped',
                    'reason': 'duplicate_etag',
                    'etag': current_etag,
                }

            # Step 4: Download Excel file
            logger.info(f"Downloading file (etag: {current_etag})")
            excel_bytes = self.webdav_client.download_file(self.file_path)
            if not excel_bytes:
                raise Exception(f"Failed to download file: {self.file_path}")

            # Step 5: Parse Excel
            parser = ExcelParser(excel_bytes)
            rows = parser.parse_rows()
            parser.close()

            logger.info(f"Parsed {len(rows)} rows from Excel")

            # Step 6: Get model class
            model_class = self._get_model_class(model_name)

            # Step 7: Process rows in transaction
            with transaction.atomic():
                for row_data in rows:
                    self._process_row(row_data, model_class, sync_state)

                # Update sync state
                sync_state.last_etag = current_etag
                sync_state.last_modified = current_modified
                sync_state.last_synced_at = timezone.now()
                sync_state.last_event_user = self.event_user
                sync_state.total_syncs += 1
                sync_state.total_conflicts += self.stats['conflicts']
                sync_state.save()

            # Step 8: Writeback __id for new records
            if self.new_records:
                self._writeback_ids(sync_state, model_class, current_etag)

            # Log completion
            duration = (timezone.now() - start_time).total_seconds()
            self._log(
                'sync_completed',
                f"Sync completed successfully in {duration:.2f}s",
                sync_state,
                details={
                    'stats': self.stats,
                    'duration_seconds': duration,
                }
            )

            logger.info(
                f"Sync completed: {self.stats['created']} created, "
                f"{self.stats['updated']} updated, {self.stats['deleted']} deleted, "
                f"{self.stats['conflicts']} conflicts, {self.stats['errors']} errors"
            )

            return {
                'status': 'success',
                'stats': self.stats,
                'etag': current_etag,
                'duration_seconds': duration,
            }

        except ExcelParseError as e:
            self._log('sync_failed', f"Excel parse error: {e}", success=False, error_message=str(e))
            logger.error(f"Excel parse error: {e}")
            raise

        except Exception as e:
            self._log('sync_failed', f"Sync failed: {e}", success=False, error_message=str(e))
            logger.error(f"Sync failed: {e}", exc_info=True)
            raise

    def _writeback_ids(self, sync_state, model_class, original_etag: str):
        """
        Write back __id values to Excel for newly created records.

        Args:
            sync_state: NextcloudSyncState instance
            model_class: Django model class
            original_etag: Original etag before writeback
        """
        try:
            logger.info(f"Writing back {len(self.new_records)} new record IDs to Excel")

            # Get all records from DB
            queryset = model_class.objects.all()
            field_mapping = ExcelGenerator.get_field_mapping(model_class.__name__)

            # Generate new Excel with IDs populated
            excel_bytes = ExcelGenerator.generate_from_queryset(queryset, field_mapping)

            # Upload to Nextcloud with etag check
            success, new_etag = self.webdav_client.upload_file(
                self.file_path,
                excel_bytes,
                check_etag=original_etag
            )

            if success:
                # Update sync state with new etag
                sync_state.last_etag = new_etag
                sync_state.save()

                self._log(
                    'excel_writeback',
                    f"Successfully wrote back {len(self.new_records)} IDs",
                    sync_state,
                    details={
                        'new_records_count': len(self.new_records),
                        'new_etag': new_etag,
                    }
                )
                logger.info(f"Successfully wrote back IDs, new etag: {new_etag}")
            else:
                # ETag mismatch - file was modified during sync
                self._log(
                    'writeback_skipped',
                    f"Writeback skipped due to etag mismatch (concurrent edit detected)",
                    sync_state,
                    details={
                        'expected_etag': original_etag,
                        'current_etag': new_etag,
                    }
                )
                logger.warning(
                    f"Writeback skipped: file was modified during sync "
                    f"(expected etag {original_etag}, found {new_etag})"
                )

        except Exception as e:
            self._log(
                'writeback_skipped',
                f"Writeback failed: {e}",
                sync_state,
                success=False,
                error_message=str(e)
            )
            logger.error(f"Writeback failed: {e}", exc_info=True)
            # Don't raise - writeback failure shouldn't fail the entire sync
