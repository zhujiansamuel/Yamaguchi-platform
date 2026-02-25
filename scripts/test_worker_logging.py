#!/usr/bin/env python3
"""
测试脚本：模拟Email Content Analysis Worker发布任务到两个Worker

此脚本用于测试:
1. Initial Order Confirmation Email Worker
2. Send Notification Email Worker

测试它们是否能正确接收并打印来自Email Content Analysis的参数
"""

import os
import sys
import django
from datetime import datetime

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

# 导入Worker类
from apps.data_acquisition.EmailParsing.initial_order_confirmation_email import InitialOrderConfirmationEmailWorker
from apps.data_acquisition.EmailParsing.send_notification_email import SendNotificationEmailWorker


def test_initial_order_confirmation_worker():
    """测试Initial Order Confirmation Email Worker"""
    print("\n" + "="*80)
    print("测试 1: Initial Order Confirmation Email Worker")
    print("="*80)
    
    # 模拟从Email Content Analysis发送的数据
    # 基于email_content_analysis.py的parse_apple_order_email函数返回的实际字段
    test_data = {
        'email_data': {
            # 邮件元数据（由execute方法添加）
            'email_id': 12345,
            'email_subject': 'ご注文ありがとうございます',
            'email_date': datetime.now().isoformat(),
            
            # parse_apple_order_email返回的字段
            'order_number': 'W123456789',
            'official_query_url': 'https://secure2.store.apple.com/shop/order/guest/vieworder?orderNumber=W123456789',
            'confirmed_at': '2024/01/15',
            
            # 商品列表（新格式）
            'line_items': [
                {
                    'product_name': 'iPhone 15 Pro Max 256GB ナチュラルチタニウム',
                    'quantity': 1,
                    'delivery': {
                        'type': 'range',
                        'start_date': '2024/01/20',
                        'end_date': '2024/01/25',
                    }
                },
                {
                    'product_name': 'USB-C - Lightningアダプタ',
                    'quantity': 2,
                    'delivery': {
                        'type': 'range',
                        'start_date': '2024/01/20',
                        'end_date': '2024/01/25',
                    }
                }
            ],
            
            # 向后兼容字段（从第一个商品提取）
            'iphone_product_names': 'iPhone 15 Pro Max 256GB ナチュラルチタニウム',
            'quantities': 1,
            'estimated_website_arrival_date': '2024/01/20',
            'estimated_website_arrival_date_2': '2024/01/25',
            
            # 配送地址
            'name': '山田太郎',
            'postal_code': '150-0001',
            'address_line_1': '東京都渋谷区神宮前',
            'address_line_2': '1-2-3 マンション名 101号室',
            
            # 联系信息
            'email': 'test@example.com',
        }
    }
    
    # 创建Worker实例并执行
    worker = InitialOrderConfirmationEmailWorker()
    result = worker.run(test_data)
    
    print(f"\n执行结果: {result}")
    print("="*80 + "\n")
    
    return result


def test_send_notification_worker():
    """测试Send Notification Email Worker"""
    print("\n" + "="*80)
    print("测试 2: Send Notification Email Worker")
    print("="*80)
    
    # 模拟从Email Content Analysis发送的数据
    # 基于email_content_analysis.py的extract_fields_from_html函数返回的实际字段
    test_data = {
        'email_data': {
            # 邮件元数据（由execute方法添加）
            'email_id': 67890,
            'email_subject': 'お客様の商品は配送中です',
            'email_date': datetime.now().isoformat(),
            
            # extract_fields_from_html返回的字段
            'order_number': 'W987654321',
            'official_query_url': 'https://secure2.store.apple.com/shop/order/guest/vieworder?orderNumber=W987654321',
            'confirmed_at': '2024/01/10',
            'estimated_website_arrival_date': '2024/01/22',
            
            # 商品列表（新格式）
            'line_items': [
                {
                    'product_name': 'MacBook Pro 14インチ M3 Pro',
                    'quantity': 1,
                    'delivery': {
                        'type': 'single',
                        'date': '2024/01/22',
                    }
                }
            ],
            
            # 向后兼容字段（从第一个商品提取）
            'iphone_product_names': 'MacBook Pro 14インチ M3 Pro',
            'quantity': 1,
            
            # 配送地址
            'postal_code': '530-0001',
            'address_line_1': '大阪府大阪市北区梅田',
            'address_line_2': '2-3-4 ビル名 5F',
            'name': '佐藤花子',
            'email': 'customer@example.jp',
            
            # 配送信息
            'tracking_number': '1234-5678-9012',
            'tracking_href': 'https://tracking.example.com/track?id=1234-5678-9012',
            'carrier_name': 'ヤマト運輸',
        }
    }
    
    # 创建Worker实例并执行
    worker = SendNotificationEmailWorker()
    result = worker.run(test_data)
    
    print(f"\n执行结果: {result}")
    print("="*80 + "\n")
    
    return result


def main():
    """主函数：运行所有测试"""
    print("\n" + "#"*80)
    print("# Worker日志测试脚本")
    print("# 测试两个Worker是否能正确接收并打印来自Email Content Analysis的参数")
    print("#"*80)
    
    try:
        # 测试Initial Order Confirmation Worker
        result1 = test_initial_order_confirmation_worker()
        
        # 测试Send Notification Worker
        result2 = test_send_notification_worker()
        
        # 汇总测试结果
        print("\n" + "#"*80)
        print("# 测试完成")
        print("#"*80)
        print(f"\nInitial Order Confirmation Worker: {result1.get('status')}")
        print(f"Send Notification Email Worker: {result2.get('status')}")
        print("\n请检查上方的日志输出,确认所有参数都已正确打印。\n")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
