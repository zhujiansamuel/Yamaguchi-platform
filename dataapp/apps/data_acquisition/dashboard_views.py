"""
Dashboard API views for data_acquisition app.

Provides read-only endpoints for the Dashboard to display
Nextcloud sync events and tracking batch progress.
"""
from collections import defaultdict
from datetime import timedelta

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.data_aggregation.authentication import SimpleTokenAuthentication
from .models import NextcloudSyncState, SyncLog, TrackingBatch
from .dashboard_serializers import (
    NextcloudSyncEventSerializer,
    NextcloudSyncGroupSerializer,
    TrackingBatchEventSerializer,
    TrackingBatchGroupSerializer,
)

# task_name → display_name mapping (sourced from TRACKING_TASK_CONFIGS + DB-driven tasks)
TASK_DISPLAY_NAMES = {
    'official_website_redirect_to_yamato_tracking': '官网 → Yamato 追踪',
    'temporary_flexible_capture': 'Temporary Flexible Capture',
    'redirect_to_japan_post_tracking': 'Redirect to Japan Post Tracking',
    'official_website_tracking': 'Official Website Tracking',
    'yamato_tracking_only': 'Yamato Tracking Only',
    'japan_post_tracking_only': 'Japan Post Tracking Only',
    'japan_post_tracking_10': 'Japan Post Tracking 10',
    'yamato_tracking_10': 'Yamato Tracking 10',
    'yamato_tracking_10_tracking_number': 'Yamato Tracking 10 (DB)',
}


class NextcloudSyncDashboardView(APIView):
    """
    GET /api/acquisition/dashboard/nextcloud-sync/?days=2

    Returns Nextcloud sync events grouped by model_name.
    """
    authentication_classes = [SimpleTokenAuthentication]

    def get(self, request):
        days = int(request.query_params.get('days', 2))
        since = timezone.now() - timedelta(days=days)

        states = NextcloudSyncState.objects.all()
        result = []

        for state in states:
            logs = SyncLog.objects.filter(
                sync_state=state,
                operation_type__in=[
                    'sync_completed', 'sync_failed', 'excel_writeback',
                ],
                created_at__gte=since,
            ).order_by('-created_at')

            if not logs.exists():
                continue

            events = NextcloudSyncEventSerializer(logs, many=True).data
            result.append({
                'model_name': state.model_name,
                'events': events,
            })

        return Response(result)


class TrackingBatchDashboardView(APIView):
    """
    GET /api/acquisition/dashboard/tracking-batches/?days=2

    Returns tracking batches grouped by task_name with source_type and label.
    """
    authentication_classes = [SimpleTokenAuthentication]

    def get(self, request):
        days = int(request.query_params.get('days', 2))
        since = timezone.now() - timedelta(days=days)

        batches = TrackingBatch.objects.filter(
            created_at__gte=since
        ).order_by('-created_at')

        # Group by task_name
        groups = defaultdict(list)
        for batch in batches:
            groups[batch.task_name].append(batch)

        result = []
        for task_name, batch_list in groups.items():
            source_type = batch_list[0].source_type if batch_list else 'excel'
            label = TASK_DISPLAY_NAMES.get(task_name, task_name)
            serialized_batches = TrackingBatchEventSerializer(batch_list, many=True).data
            result.append({
                'task_name': task_name,
                'source_type': source_type,
                'label': label,
                'batches': serialized_batches,
            })

        return Response(result)
