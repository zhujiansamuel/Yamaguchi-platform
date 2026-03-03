"""
Dashboard API views for data_aggregation app.

Provides read-only endpoint for the Dashboard to display
email processing pipeline status.
"""
from collections import defaultdict
from datetime import timedelta

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from .authentication import SimpleTokenAuthentication
from .models import EmailProcessingLog
from .dashboard_serializers import EmailBatchSerializer

# stage → Chinese label mapping (from EmailProcessingLog.STAGE_CHOICES)
STAGE_LABELS = dict(EmailProcessingLog.STAGE_CHOICES)


class EmailTaskDashboardView(APIView):
    """
    GET /api/aggregation/dashboard/email-tasks/?days=2

    Returns email processing logs grouped by stage.
    """
    authentication_classes = [SimpleTokenAuthentication]

    def get(self, request):
        days = int(request.query_params.get('days', 2))
        since = timezone.now() - timedelta(days=days)

        logs = EmailProcessingLog.objects.filter(
            created_at__gte=since
        ).order_by('-created_at')

        # Group by stage
        groups = defaultdict(list)
        for log in logs:
            groups[log.stage].append(log)

        result = []
        for stage, _ in EmailProcessingLog.STAGE_CHOICES:
            batch_list = groups.get(stage, [])
            serialized = EmailBatchSerializer(batch_list, many=True).data
            result.append({
                'stage': stage,
                'label': STAGE_LABELS.get(stage, stage),
                'batches': serialized,
            })

        return Response(result)
