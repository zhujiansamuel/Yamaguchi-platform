import pandas as pd
import numpy as np
import logging
import uuid
import re
from datetime import datetime
from django.db import transaction
from apps.data_aggregation.models import Purchasing, OfficialAccount

logger = logging.getLogger(__name__)


def safe_str(value):
    """将值安全转换为字符串，处理 NaN 和 None"""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if pd.isna(value):
        return None
    return str(value).strip() if value else None


def parse_date_from_japanese(date_str):
    """
    从日文日期字符串中提取日期
    支持格式:
    - "配送済み 2026年1月11日"
    - "2026年1月11日"
    - "2026/01/10"
    """
    if not date_str:
        return None

    date_str = str(date_str).strip()

    # 匹配 "YYYY年M月D日" 格式
    match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
    if match:
        try:
            year, month, day = match.groups()
            return datetime(int(year), int(month), int(day)).date()
        except ValueError:
            pass

    # 匹配 "YYYY/MM/DD" 格式
    match = re.match(r'(\d{4})/(\d{1,2})/(\d{1,2})', date_str)
    if match:
        try:
            year, month, day = match.groups()
            return datetime(int(year), int(month), int(day)).date()
        except ValueError:
            pass

    return None


def parse_datetime(datetime_str):
    """解析日期时间字符串为 datetime 对象"""
    if not datetime_str:
        return None

    datetime_str = str(datetime_str).strip()

    # 处理 "2026-01-10 17:43:32" 格式
    try:
        return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        pass

    # 处理 "2025/12/17 10:34" 格式 (状態発生日)
    try:
        return datetime.strptime(datetime_str, '%Y/%m/%d %H:%M')
    except ValueError:
        pass

    return None


@transaction.atomic
def redirect_to_japan_post_tracking(df: pd.DataFrame) -> bool:
    """
    处理重定向到 Japan Post 的追踪数据

    Args:
        df: 包含 Japan Post 追踪数据的 DataFrame

    Returns:
        bool: 处理是否成功
    """
    if df.empty:
        logger.warning("Received empty DataFrame")
        return False

    # 1. 找到"配送履歴"不为空的最后一行
    # 过滤出"配送履歴"列不为空的行
    valid_rows = df[df['配送履歴'].notna() & (df['配送履歴'] != '')]

    if valid_rows.empty:
        logger.warning("No valid rows found with non-empty '配送履歴'")
        return False

    # 获取最后一行
    last_row = valid_rows.iloc[-1]

    # 提取字段
    order_number = safe_str(last_row.get('web_scraper_start_url'))
    tracking_number = safe_str(last_row.get('category-link-0'))
    email = safe_str(last_row.get('email'))
    office_account = safe_str(last_row.get('office_account'))
    iphone_type = safe_str(last_row.get('iphone_type'))
    latest_delivery_status = safe_str(last_row.get('配送履歴'))
    estimated_delivery_date_str = safe_str(last_row.get('estimated_delivery_date'))
    time_scraped_str = safe_str(last_row.get('time-scraped'))
    status_date_str = safe_str(last_row.get('状態発生日'))  # 配送状態发生时间
    confirmed_at_str = safe_str(last_row.get('confirmed_at'))  # 订单确认时间

    # 解析日期
    estimated_delivery_date = parse_date_from_japanese(estimated_delivery_date_str)
    last_info_updated_at = parse_datetime(time_scraped_str)
    delivery_status_query_time = parse_datetime(status_date_str)  # 解析状態発生日
    confirmed_at = parse_datetime(confirmed_at_str) if confirmed_at_str else None

    if not order_number:
        logger.error("Order number (web_scraper_start_url) is missing in the last valid row")
        return False

    if not email:
        logger.error(f"Email is missing for order {order_number}")
        return False

    # 2. 查询与 order_number 相同的 Purchasing 实例
    try:
        purchasing = Purchasing.objects.filter(order_number=order_number).first()

        if purchasing:
            logger.info(f"Found existing Purchasing: {order_number}")
            # 2-A: Purchasing 实例存在
            if purchasing.official_account:
                # 2-A-A & 2-A-B: 检查 email 是否相同
                if purchasing.official_account.email != email:
                    logger.error(
                        f"Email mismatch for order {order_number}: "
                        f"DB email {purchasing.official_account.email}, DF email {email}"
                    )
                    # 抛出异常后继续执行步骤4的更新（按用户要求）
            else:
                # 2-A-C: 没有关联的 official_account
                official_account = OfficialAccount.objects.filter(email=email).first()

                if official_account:
                    # official_account 存在，建立关联
                    purchasing.official_account = official_account
                    purchasing.save()
                    logger.info(f"Associated existing OfficialAccount {email} with Purchasing {order_number}")
                else:
                    # official_account 不存在，创建新的
                    official_account = OfficialAccount.objects.create(
                        email=email,
                        name=office_account or '',
                        passkey='111111',
                        account_id=str(uuid.uuid4())[:8]
                    )
                    logger.info(f"Created new OfficialAccount: {email}")

                    purchasing.official_account = official_account
                    purchasing.save()
                    logger.info(f"Associated new OfficialAccount {email} with Purchasing {order_number}")
        else:
            # 2-B: Purchasing 实例不存在
            # 先查询 email 对应的 official_account
            official_account = OfficialAccount.objects.filter(email=email).first()

            if not official_account:
                # 2-B-B: official_account 不存在，创建新的
                official_account = OfficialAccount.objects.create(
                    email=email,
                    name=office_account or '',
                    passkey='111111',
                    account_id=str(uuid.uuid4())[:8]
                )
                logger.info(f"Created new OfficialAccount: {email}")

            # 3. 使用 Purchasing.create_with_inventory() 建立新的 Purchasing 实例
            purchasing, _ = Purchasing.create_with_inventory(
                email=email,
                inventory_count=1,
                iphone_type_name=iphone_type,
                order_number=order_number  # 显式传入 order_number 避免自动生成
            )
            logger.info(f"Created Purchasing {order_number} with OfficialAccount {email}")

        # 4. 清理现有的无效 tracking_number（如果存在）
        # 这样可以避免冲突检测阻止更新
        if purchasing.tracking_number in ['nan', 'None', 'null', 'NaN', '']:
            purchasing.tracking_number = ''
            purchasing.save(update_fields=['tracking_number'])
            logger.info(f"Cleaned invalid tracking_number for order {order_number}")

        # 5. 更新实例字段
        # 注意：CSV中的estimated_delivery_date字段实际对应到Purchasing.estimated_website_arrival_date
        # 这是因为Japan Post追踪数据中的预计送达日期是指官网到货日期，而非最终配送日期
        update_data = {
            'order_number': order_number,
            'tracking_number': tracking_number,
            'estimated_website_arrival_date': estimated_delivery_date,  # CSV的estimated_delivery_date -> DB的estimated_website_arrival_date
            'latest_delivery_status': latest_delivery_status[:10] if latest_delivery_status else None,  # 限制最大长度为10
            'last_info_updated_at': last_info_updated_at,
            'delivery_status_query_time': delivery_status_query_time,  # CSV的状態発生日 -> DB的delivery_status_query_time
            'delivery_status_query_source': 'redirect_to_japan_post_tracking'
        }
        
        # 如果存在 confirmed_at 列且解析成功，则添加到更新字典中
        if confirmed_at:
            update_data['confirmed_at'] = confirmed_at
        
        purchasing.update_fields(**update_data)

        # 6. 解锁记录
        purchasing.is_locked = False
        purchasing.locked_at = None
        purchasing.locked_by_worker = 'unlock'
        purchasing.save(update_fields=['is_locked', 'locked_at', 'locked_by_worker'])

        logger.info(
            f"Updated and saved Purchasing {order_number}: "
            f"tracking={purchasing.tracking_number}, "
            f"status={purchasing.latest_delivery_status}, "
            f"unlocked=True"
        )
        return True

    except Exception as e:
        logger.exception(f"Error processing Japan Post tracking data: {str(e)}")
        return False