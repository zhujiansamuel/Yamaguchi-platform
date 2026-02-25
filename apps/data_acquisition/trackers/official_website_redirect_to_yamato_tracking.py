import pandas as pd
import numpy as np
import logging
import uuid
import re
from datetime import datetime, timedelta
from django.db import transaction
from django.conf import settings
from apps.data_aggregation.models import Purchasing, OfficialAccount

logger = logging.getLogger(__name__)


def safe_str(value):
    """将值安全转换为字符串，处理 NaN 和 None"""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if pd.isna(value):
        return None
    return str(value).strip() if value else None

def parse_date(date_str):
    """解析日期字符串为 date 对象"""
    if not date_str or date_str == '-':
        return None
    
    # 处理 "2025年12月17日" 格式
    if '年' in date_str and '月' in date_str and '日' in date_str:
        try:
            return datetime.strptime(date_str, '%Y年%m月%d日').date()
        except ValueError:
            pass
            
    # 处理 "2026-01-08 10:55:42" 格式
    try:
        return datetime.strptime(date_str.split(' ')[0], '%Y-%m-%d').date()
    except (ValueError, IndexError):
        pass
        
    return None

def parse_datetime(datetime_str, reference_date=None):
    """解析日期时间字符串为 datetime 对象

    支持以下格式：
    1. "2026-01-08 10:55:42" - 完整日期时间
    2. "12月19日 19:10" - 日语格式（无年份，需要推断）

    Args:
        datetime_str: 日期时间字符串
        reference_date: 参考日期（用于推断年份），可以是 date 或 datetime 对象

    Returns:
        datetime 对象或 None
    """
    if not datetime_str or datetime_str == '-':
        return None

    # 尝试解析标准格式 "2026-01-08 10:55:42"
    try:
        return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        pass

    # 尝试解析日语格式 "12月19日 19:10"
    try:
        # 使用正则提取月、日、时、分
        match = re.match(r'(\d+)月(\d+)日\s+(\d+):(\d+)', datetime_str)
        if match:
            month, day, hour, minute = map(int, match.groups())

            # 推断年份
            if reference_date:
                # 使用参考日期的年份
                if isinstance(reference_date, datetime):
                    year = reference_date.year
                else:
                    year = reference_date.year
            else:
                # 使用当前年份
                year = datetime.now().year

            return datetime(year, month, day, hour, minute)
    except (ValueError, AttributeError):
        pass

    return None

@transaction.atomic
def official_website_redirect_to_yamato_tracking(df: pd.DataFrame) -> bool:
    if df.empty:
        logger.warning("Received empty DataFrame")
        return False

    # 1. 过滤掉 category-link-0 为空的所有行
    # 检查 category-link-0 列是否存在
    if 'category-link-0' in df.columns:
        # 过滤掉 category-link-0 为空的行（NaN、None、空字符串等）
        filtered_df = df[df['category-link-0'].notna() & (df['category-link-0'].astype(str).str.strip() != '')]

        if filtered_df.empty:
            logger.warning("All rows have empty 'category-link-0'")
            return False

        logger.info(f"Filtered DataFrame: {len(df)} rows -> {len(filtered_df)} rows (removed empty 'category-link-0')")
    else:
        logger.warning("Column 'category-link-0' not found, using original DataFrame")
        filtered_df = df

    # 2. 读取过滤后 df 的最后一行
    last_row = filtered_df.iloc[-1]

    # 提取字段，使用 safe_str 处理
    order_number = safe_str(last_row.get('order_number'))
    email = safe_str(last_row.get('email'))
    name = safe_str(last_row.get('office_account'))
    iphone_type = safe_str(last_row.get('iphone_type'))
    tracking_number = safe_str(last_row.get('category-link-0'))
    latest_delivery_status = safe_str(last_row.get('data2'))
    order_date_str = safe_str(last_row.get('order_date'))
    official_website_arrival_time_str = safe_str(last_row.get('Official-website-arrival-time'))
    estimated_delivery_date_str = safe_str(last_row.get('estimated_delivery_date'))
    time_scraped_str = safe_str(last_row.get('time-scraped'))
    data3_str = safe_str(last_row.get('data3'))

    if not order_number:
        logger.error("Order number is missing in the last row of DataFrame")
        return False

    # 2. 查询 Purchasing 实例
    try:
        purchasing = Purchasing.objects.filter(order_number=order_number).first()

        if purchasing:
            logger.info(f"Found existing Purchasing: {order_number}")

            # 检查是否在配置的时间间隔内已经发布过，避免重复发布
            # if purchasing.last_info_updated_at:
            #     query_interval_hours = getattr(settings, 'DELIVERY_STATUS_QUERY_INTERVAL_HOURS', 6)
            #     time_threshold = datetime.now() - timedelta(hours=query_interval_hours)
            #     if purchasing.last_info_updated_at > time_threshold:
            #         logger.info(f"Skipping order {order_number}: already published within {query_interval_hours} hours (last updated at {purchasing.last_info_updated_at})")
            #         return True

            # 2-A: Purchasing 实例存在
            if purchasing.official_account:
                # 2-A-A & 2-A-B: 检查 email 是否相同
                if purchasing.official_account.email != email:
                    logger.error(f"Email mismatch for order {order_number}: DB email {purchasing.official_account.email}, DF email {email}")
                    # 抛出异常后继续执行（按用户要求记录日志）
            else:
                # 2-A-C: 没有关联的 official_account
                official_account, created = OfficialAccount.objects.get_or_create(
                    email=email,
                    defaults={
                        'name': name,
                        'passkey': '111111',
                        'account_id': str(uuid.uuid4())[:8]
                    }
                )
                if created:
                    logger.info(f"Created OfficialAccount: {email}")

                purchasing.official_account = official_account
                purchasing.save()
                logger.info(f"Associated Purchasing {order_number} with OfficialAccount {email}")
        else:
            # 2-B: Purchasing 实例不存在
            official_account, created = OfficialAccount.objects.get_or_create(
                email=email,
                defaults={
                    'name': name,
                    'passkey': '111111',
                    'account_id': str(uuid.uuid4())[:8]
                }
            )
            if created:
                logger.info(f"Created OfficialAccount: {email}")

            # 3. 使用 Purchasing.create_with_inventory() 建立新的 Purchasing 实例
            # 注意：create_with_inventory 返回 (instance, inventory_list)
            purchasing, _ = Purchasing.create_with_inventory(
                email=email,
                inventory_count=1,
                iphone_type_name=iphone_type,
                order_number=order_number # 显式传入 order_number 避免自动生成
            )
            logger.info(f"Created Purchasing {order_number} with OfficialAccount {email}")

        # 4. 清理现有的无效 tracking_number（如果存在）
        # 这样可以避免冲突检测阻止更新
        if purchasing.tracking_number in ['nan', 'None', 'null', 'NaN', '']:
            purchasing.tracking_number = ''
            purchasing.save(update_fields=['tracking_number'])
            logger.info(f"Cleaned invalid tracking_number for order {order_number}")

        # 5. 更新实例字段
        # 解析日期和时间
        order_date_obj = parse_date(order_date_str)
        confirmed_at_value = None
        if order_date_obj:
            confirmed_at_value = datetime.combine(order_date_obj, datetime.min.time())

        estimated_website_arrival_date_value = parse_date(official_website_arrival_time_str)
        estimated_delivery_date_value = parse_date(estimated_delivery_date_str)
        last_info_updated_at_value = parse_datetime(time_scraped_str)

        # 使用 order_date 或 time-scraped 作为参考日期来解析 data3（日语格式）
        # 优先使用 order_date，因为配送状态查询时间通常发生在订单日期的同一年
        reference_date = order_date_obj or last_info_updated_at_value
        delivery_status_query_time_value = parse_datetime(data3_str, reference_date)

        update_data = {
            'order_number': order_number,
            'confirmed_at': confirmed_at_value,
            'tracking_number': tracking_number,
            'estimated_delivery_date': estimated_delivery_date_value,  # CSV的estimated_delivery_date -> DB的estimated_delivery_date
            'latest_delivery_status': latest_delivery_status[:10] if latest_delivery_status else None,  # 模型限制 max_length=10
            'last_info_updated_at': last_info_updated_at_value,
            'estimated_website_arrival_date': estimated_website_arrival_date_value,  # CSV的Official-website-arrival-time -> DB of estimated_website_arrival_date
            'delivery_status_query_time': delivery_status_query_time_value,  # CSV的data3 -> DB的delivery_status_query_time
            'delivery_status_query_source': 'official_website_redirect_to_yamato_tracking'
        }
        
        purchasing.update_fields(**update_data)

        # 6. 解锁记录
        purchasing.is_locked = False
        purchasing.locked_at = None
        purchasing.locked_by_worker = 'unlock'
        purchasing.save(update_fields=['is_locked', 'locked_at', 'locked_by_worker'])

        logger.info(f"Updated and saved Purchasing {order_number}: tracking={purchasing.tracking_number}, unlocked=True")
        return True

    except Exception as e:
        logger.exception(f"Error processing yamato tracking data: {str(e)}")
        return False
