#!/usr/bin/env python
"""
测试Email Content Analysis Worker的Apple订单邮件解析功能

使用方法:
python test_email_parsing.py
"""

import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apps.settings')
django.setup()

from apps.data_acquisition.EmailParsing.email_content_analysis import (
    EmailContentAnalysisWorker,
    parse_apple_order_email,
)


def test_worker():
    """测试Email Content Analysis Worker"""
    print("=" * 80)
    print("测试 Email Content Analysis Worker")
    print("=" * 80)

    worker = EmailContentAnalysisWorker()

    # 执行worker
    result = worker.run({})

    print("\n执行结果:")
    print(f"状态: {result.get('status')}")

    if result.get('status') == 'success':
        extracted_data = result.get('result', {}).get('extracted_data', {})
        print("\n提取的数据:")
        print(f"  - 邮件ID: {extracted_data.get('email_id')}")
        print(f"  - 订单号: {extracted_data.get('order_number')}")
        print(f"  - 官方查询URL: {extracted_data.get('official_query_url')}")
        print(f"  - 确认时间: {extracted_data.get('confirmed_at')}")
        print(f"  - 预计到达日期: {extracted_data.get('estimated_website_arrival_date')}")
        print(f"  - 预计到达日期2: {extracted_data.get('estimated_website_arrival_date_2')}")
        print(f"  - 产品名称: {extracted_data.get('iphone_product_names')}")
        print(f"  - 数量: {extracted_data.get('quantities')}")
        print(f"  - 邮箱: {extracted_data.get('email')}")
        print(f"  - 姓名: {extracted_data.get('name')}")
        print(f"  - 邮编: {extracted_data.get('postal_code')}")
        print(f"  - 地址行1: {extracted_data.get('address_line_1')}")
        print(f"  - 地址行2: {extracted_data.get('address_line_2')}")
    elif result.get('status') == 'no_email':
        print("\n未找到符合条件的邮件")
        print("请确保数据库中存在:")
        print("  - Subject包含'ご注文ありがとうございます'")
        print("  - From address是'order_acknowledgment@orders.apple.com'")
        print("  - 有对应的MailMessageBody")
    else:
        print(f"\n错误信息: {result.get('message')}")
        if 'error' in result:
            print(f"错误详情: {result.get('error')}")

    print("\n" + "=" * 80)


def test_html_parsing():
    """测试HTML解析函数（使用示例HTML）"""
    print("\n" + "=" * 80)
    print("测试 HTML 解析函数")
    print("=" * 80)

    # 示例HTML（简化版）
    sample_html = """
    <html>
        <body>
            <div class="order-num">
                <span>2024/01/15</span>
            </div>
            <a class="aapl-link" href="https://secure2.store.apple.com/vieworder?orderId=W1234567890">
                W1234567890
            </a>
            <span>お届け予定日：2024/01/20 - 2024/01/25</span>
            <td class="product-name-td">iPhone 15 Pro Max 256GB ナチュラルチタニウム</td>
            <td class="product-quantity">1</td>
            <h3>お届け先住所</h3>
            <div class="gen-txt">
                123-4567
                東京都
                渋谷区神南1-2-3
                山田太郎
            </div>
            <div>test@example.com</div>
        </body>
    </html>
    """

    result = parse_apple_order_email(sample_html)

    if result:
        print("\n解析成功！提取的数据:")
        for key, value in result.items():
            print(f"  - {key}: {value}")
    else:
        print("\n解析失败")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    print("\n开始测试...\n")

    # 测试HTML解析函数
    test_html_parsing()

    # 测试完整的worker
    test_worker()

    print("\n测试完成！\n")
