"""
Batch Tracker Utility Functions

提供查询和监控追踪批次（TrackingBatch）的工具函数。
用于实时查看 Excel 文件中所有 URL 的爬取完成状态。

使用示例：

    from apps.data_acquisition.batch_tracker import (
        get_batch_by_uuid,
        get_batch_by_file_path,
        list_batches,
        get_pending_batches,
        get_batch_summary,
    )

    # 1. 通过批次 UUID 查询
    batch = get_batch_by_uuid('a1b2c3d4-e5f6-7890-abcd-ef1234567890')
    if batch:
        print(f"完成度: {batch.completion_percentage}%")
        print(f"已完成: {batch.completed_jobs}/{batch.total_jobs}")

    # 2. 通过文件路径查询
    batch = get_batch_by_file_path('/official_website_redirect_to_yamato_tracking/OWRYT-20260108-001.xlsx')

    # 3. 列出所有批次
    batches = list_batches(task_name='official_website_redirect_to_yamato_tracking', days=7)

    # 4. 查询未完成的批次
    pending = get_pending_batches()

    # 5. 获取详细统计
    summary = get_batch_summary(batch)
    print(summary)
"""

from typing import Optional, List, Dict, Any
from django.utils import timezone
from datetime import timedelta
from .models import TrackingBatch, TrackingJob


def get_batch_by_uuid(batch_uuid: str) -> Optional[TrackingBatch]:
    """
    通过批次 UUID 查询 TrackingBatch

    Args:
        batch_uuid: 完整的批次 UUID 字符串或前8位短格式

    Returns:
        TrackingBatch 对象，如果不存在则返回 None

    示例:
        batch = get_batch_by_uuid('a1b2c3d4-e5f6-7890-abcd-ef1234567890')
        batch = get_batch_by_uuid('a1b2c3d4')  # 短格式
    """
    try:
        # 尝试精确匹配
        return TrackingBatch.objects.get(batch_uuid=batch_uuid)
    except (TrackingBatch.DoesNotExist, ValueError):
        # 如果是短格式（8位），尝试模糊匹配
        if len(batch_uuid) == 8:
            batches = TrackingBatch.objects.filter(
                batch_uuid__startswith=batch_uuid
            )
            if batches.exists():
                return batches.first()
    return None


def get_batch_by_file_path(file_path: str, latest: bool = True) -> Optional[TrackingBatch]:
    """
    通过文件路径查询 TrackingBatch

    Args:
        file_path: Nextcloud 文件路径
        latest: 是否返回最新的批次（如果文件被多次处理）

    Returns:
        TrackingBatch 对象，如果不存在则返回 None

    示例:
        batch = get_batch_by_file_path('/official_website_redirect_to_yamato_tracking/OWRYT-20260108-001.xlsx')
    """
    batches = TrackingBatch.objects.filter(file_path=file_path).order_by('-created_at')
    if batches.exists():
        return batches.first() if latest else batches
    return None


def list_batches(
    task_name: Optional[str] = None,
    status: Optional[str] = None,
    days: int = 7
) -> List[TrackingBatch]:
    """
    列出追踪批次

    Args:
        task_name: 过滤特定任务类型（可选）
        status: 过滤特定状态（可选）: pending, processing, completed, partial
        days: 查询最近多少天的批次（默认7天）

    Returns:
        TrackingBatch 列表

    示例:
        # 查询最近7天所有批次
        batches = list_batches()

        # 查询特定任务类型
        batches = list_batches(task_name='official_website_redirect_to_yamato_tracking')

        # 查询未完成的批次
        batches = list_batches(status='processing', days=30)
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    queryset = TrackingBatch.objects.filter(created_at__gte=cutoff_date)

    if task_name:
        queryset = queryset.filter(task_name=task_name)

    if status:
        queryset = queryset.filter(status=status)

    return list(queryset.order_by('-created_at'))


def get_pending_batches(days: int = 30) -> List[TrackingBatch]:
    """
    获取所有未完成的批次

    Args:
        days: 查询最近多少天（默认30天）

    Returns:
        未完成的 TrackingBatch 列表

    示例:
        pending = get_pending_batches()
        for batch in pending:
            print(f"{batch.file_path}: {batch.completion_percentage}% 完成")
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    return list(
        TrackingBatch.objects.filter(
            created_at__gte=cutoff_date,
            status__in=['pending', 'processing']
        ).order_by('-created_at')
    )


def get_batch_summary(batch: TrackingBatch) -> Dict[str, Any]:
    """
    获取批次的详细统计信息

    Args:
        batch: TrackingBatch 对象

    Returns:
        包含详细统计信息的字典

    示例:
        batch = get_batch_by_uuid('a1b2c3d4')
        summary = get_batch_summary(batch)
        print(summary)
    """
    # 刷新统计数据（确保数据最新）
    batch.refresh_from_db()

    # 获取任务列表
    jobs = batch.jobs.all()
    pending_jobs = [j for j in jobs if j.status == 'pending']
    completed_jobs = [j for j in jobs if j.status == 'completed']
    failed_jobs = [j for j in jobs if j.status == 'failed']

    # 计算耗时
    duration = None
    if batch.completed_at:
        duration = (batch.completed_at - batch.created_at).total_seconds()
    else:
        duration = (timezone.now() - batch.created_at).total_seconds()

    return {
        'batch_uuid': str(batch.batch_uuid),
        'batch_short': str(batch.batch_uuid)[:8],
        'task_name': batch.task_name,
        'file_path': batch.file_path,
        'status': batch.status,
        'status_display': batch.get_status_display(),

        # 进度统计
        'total_jobs': batch.total_jobs,
        'completed_jobs': batch.completed_jobs,
        'failed_jobs': batch.failed_jobs,
        'pending_jobs': batch.pending_jobs,
        'completion_percentage': batch.completion_percentage,
        'is_completed': batch.is_completed,

        # 时间信息
        'created_at': batch.created_at,
        'updated_at': batch.updated_at,
        'completed_at': batch.completed_at,
        'duration_seconds': int(duration) if duration else None,

        # 任务详情
        'pending_job_ids': [j.custom_id for j in pending_jobs],
        'failed_job_ids': [j.custom_id for j in failed_jobs],
        'failed_job_errors': [
            {'custom_id': j.custom_id, 'error': j.error_message}
            for j in failed_jobs if j.error_message
        ],
    }


def get_batch_jobs(batch: TrackingBatch, status: Optional[str] = None) -> List[TrackingJob]:
    """
    获取批次中的任务列表

    Args:
        batch: TrackingBatch 对象
        status: 过滤特定状态（可选）: pending, completed, failed

    Returns:
        TrackingJob 列表

    示例:
        # 获取所有任务
        all_jobs = get_batch_jobs(batch)

        # 获取失败的任务
        failed = get_batch_jobs(batch, status='failed')
    """
    queryset = batch.jobs.all()

    if status:
        queryset = queryset.filter(status=status)

    return list(queryset.order_by('index'))


def print_batch_status(batch: TrackingBatch, show_jobs: bool = False):
    """
    打印批次状态（用于调试）

    Args:
        batch: TrackingBatch 对象
        show_jobs: 是否显示所有任务详情

    示例:
        batch = get_batch_by_uuid('a1b2c3d4')
        print_batch_status(batch, show_jobs=True)
    """
    summary = get_batch_summary(batch)

    print(f"\n{'='*80}")
    print(f"Batch: {summary['batch_short']} ({summary['status_display']})")
    print(f"{'='*80}")
    print(f"Task:      {summary['task_name']}")
    print(f"File:      {summary['file_path']}")
    print(f"UUID:      {summary['batch_uuid']}")
    print(f"\nProgress:")
    print(f"  Total:     {summary['total_jobs']}")
    print(f"  Completed: {summary['completed_jobs']}")
    print(f"  Failed:    {summary['failed_jobs']}")
    print(f"  Pending:   {summary['pending_jobs']}")
    print(f"  Progress:  {summary['completion_percentage']}%")
    print(f"\nTiming:")
    print(f"  Created:   {summary['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
    if summary['completed_at']:
        print(f"  Completed: {summary['completed_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Duration:  {summary['duration_seconds']}s")
    else:
        print(f"  Duration:  {summary['duration_seconds']}s (ongoing)")

    if summary['failed_job_errors']:
        print(f"\nFailed Jobs:")
        for error in summary['failed_job_errors']:
            print(f"  - {error['custom_id']}: {error['error']}")

    if show_jobs:
        jobs = get_batch_jobs(batch)
        print(f"\nAll Jobs:")
        for job in jobs:
            status_icon = {
                'pending': '⏳',
                'completed': '✅',
                'failed': '❌'
            }.get(job.status, '?')
            print(f"  {status_icon} [{job.index:04d}] {job.custom_id} - {job.status}")

    print(f"{'='*80}\n")


def get_task_statistics(task_name: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
    """
    获取任务类型的统计信息

    Args:
        task_name: 任务名称（可选，不指定则统计所有任务）
        days: 统计最近多少天（默认30天）

    Returns:
        统计信息字典

    示例:
        # 统计特定任务
        stats = get_task_statistics('official_website_redirect_to_yamato_tracking', days=7)
        print(f"最近7天处理了 {stats['total_batches']} 个批次")

        # 统计所有任务
        all_stats = get_task_statistics(days=30)
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    queryset = TrackingBatch.objects.filter(created_at__gte=cutoff_date)

    if task_name:
        queryset = queryset.filter(task_name=task_name)

    total_batches = queryset.count()
    completed_batches = queryset.filter(status='completed').count()
    partial_batches = queryset.filter(status='partial').count()
    processing_batches = queryset.filter(status='processing').count()
    pending_batches = queryset.filter(status='pending').count()

    total_jobs = sum(b.total_jobs for b in queryset)
    completed_jobs = sum(b.completed_jobs for b in queryset)
    failed_jobs = sum(b.failed_jobs for b in queryset)

    return {
        'task_name': task_name or 'all',
        'days': days,
        'total_batches': total_batches,
        'completed_batches': completed_batches,
        'partial_batches': partial_batches,
        'processing_batches': processing_batches,
        'pending_batches': pending_batches,
        'total_jobs': total_jobs,
        'completed_jobs': completed_jobs,
        'failed_jobs': failed_jobs,
        'pending_jobs': total_jobs - completed_jobs - failed_jobs,
        'success_rate': round((completed_jobs / total_jobs * 100), 2) if total_jobs > 0 else 0,
    }
