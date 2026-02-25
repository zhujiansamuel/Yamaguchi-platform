#!/usr/bin/env python3
"""
诊断脚本：检查 Yamato Tracking 10 任务的执行状态
"""
import os
import sys
import django

# 设置 Django 环境
sys.path.insert(0, '/home/ubuntu/Data-consolidation')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.data_acquisition.models import TrackingBatch, TrackingJob

def check_latest_batch():
    """检查最新的 yamato_tracking_10 批次"""
    print("=" * 80)
    print("检查最新的 Yamato Tracking 10 批次")
    print("=" * 80)
    
    # 查找最新的 yamato_tracking_10 批次
    batch = TrackingBatch.objects.filter(
        task_name='yamato_tracking_10'
    ).order_by('-created_at').first()
    
    if not batch:
        print("❌ 没有找到任何 yamato_tracking_10 批次")
        return
    
    print(f"\n📦 批次信息:")
    print(f"   UUID: {batch.batch_uuid}")
    print(f"   文件路径: {batch.file_path}")
    print(f"   状态: {batch.status}")
    print(f"   总任务数: {batch.total_jobs}")
    print(f"   已完成: {batch.completed_jobs}")
    print(f"   失败: {batch.failed_jobs}")
    print(f"   创建时间: {batch.created_at}")
    print(f"   完成时间: {batch.completed_at}")
    print(f"   写回已触发: {batch.writeback_triggered}")
    print(f"   写回完成时间: {batch.writeback_completed_at}")
    
    # 查询所有相关的 TrackingJob
    jobs = TrackingJob.objects.filter(batch=batch).order_by('index')
    
    print(f"\n📋 任务详情 (共 {jobs.count()} 个):")
    print(f"{'序号':<6} {'状态':<12} {'追踪号':<20} {'写回数据':<15} {'完成时间'}")
    print("-" * 80)
    
    for job in jobs:
        status_emoji = {
            'pending': '⏳',
            'completed': '✅',
            'failed': '❌',
            'redirected': '↪️'
        }.get(job.status, '❓')
        
        writeback_preview = (job.writeback_data[:12] if job.writeback_data else '-')
        completed_time = job.completed_at.strftime('%H:%M:%S') if job.completed_at else '-'
        
        print(f"{job.index:<6} {status_emoji} {job.status:<10} {job.target_url:<20} {writeback_preview:<15} {completed_time}")
    
    # 统计分析
    print(f"\n📊 状态统计:")
    status_counts = {}
    for job in jobs:
        status_counts[job.status] = status_counts.get(job.status, 0) + 1
    
    for status, count in sorted(status_counts.items()):
        print(f"   {status}: {count}")
    
    # 检查是否有 pending 的任务
    pending_jobs = jobs.filter(status='pending')
    if pending_jobs.exists():
        print(f"\n⚠️  警告：还有 {pending_jobs.count()} 个任务处于 pending 状态")
        print(f"   索引: {list(pending_jobs.values_list('index', flat=True))}")
    
    # 检查写回数据
    jobs_with_writeback = jobs.exclude(writeback_data__isnull=True).exclude(writeback_data='')
    jobs_without_writeback = jobs.filter(status='completed').filter(
        models.Q(writeback_data__isnull=True) | models.Q(writeback_data='')
    )
    
    print(f"\n📝 写回数据统计:")
    print(f"   有写回数据: {jobs_with_writeback.count()}")
    print(f"   已完成但无写回数据: {jobs_without_writeback.count()}")
    
    if jobs_without_writeback.exists():
        print(f"   ⚠️  这些已完成的任务没有写回数据:")
        for job in jobs_without_writeback:
            print(f"      - 索引 {job.index}: {job.target_url}")

if __name__ == '__main__':
    from django.db import models
    check_latest_batch()
