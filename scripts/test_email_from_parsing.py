#!/usr/bin/env python
"""
Test script to verify email from header parsing logic.
测试脚本以验证邮件 from 头部解析逻辑。
"""
from email.utils import parseaddr


def parse_from_header(raw_from):
    """
    Parse from header to extract email address and name.
    解析 from 头部以提取邮箱地址和姓名。

    Args:
        raw_from: Raw from header string (e.g., "From: Apple Store <order_acknowledgment@orders.apple.com>")

    Returns:
        tuple: (from_address, from_name)
    """
    from_address = ''
    from_name = ''

    if raw_from:
        # Remove "From: " prefix if present
        if raw_from.startswith('From: '):
            raw_from = raw_from[6:]  # Remove "From: "

        # Parse the email address and name using parseaddr
        parsed_name, parsed_address = parseaddr(raw_from)
        from_address = parsed_address
        from_name = parsed_name

    return from_address, from_name


def test_parsing():
    """Run test cases for from header parsing."""
    test_cases = [
        {
            "input": "From: Apple Store <order_acknowledgment@orders.apple.com>",
            "expected_address": "order_acknowledgment@orders.apple.com",
            "expected_name": "Apple Store",
            "description": "Standard format with name and angle brackets"
        },
        {
            "input": "From: Apple Store <shipping_notification_jp@orders.apple.com>",
            "expected_address": "shipping_notification_jp@orders.apple.com",
            "expected_name": "Apple Store",
            "description": "Apple Store shipping notification"
        },
        {
            "input": "From: <no-reply@example.com>",
            "expected_address": "no-reply@example.com",
            "expected_name": "",
            "description": "Email only with angle brackets, no name"
        },
        {
            "input": "From: user@example.com",
            "expected_address": "user@example.com",
            "expected_name": "",
            "description": "Email only without angle brackets"
        },
        {
            "input": "From: \"John Doe\" <john.doe@example.com>",
            "expected_address": "john.doe@example.com",
            "expected_name": "John Doe",
            "description": "Name in quotes"
        },
        {
            "input": "",
            "expected_address": "",
            "expected_name": "",
            "description": "Empty string"
        }
    ]

    print("Testing email from header parsing...\n")
    print("=" * 80)

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        input_str = test_case["input"]
        expected_address = test_case["expected_address"]
        expected_name = test_case["expected_name"]
        description = test_case["description"]

        from_address, from_name = parse_from_header(input_str)

        # Check if results match expected values
        address_match = from_address == expected_address
        name_match = from_name == expected_name

        if address_match and name_match:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1

        print(f"\nTest {i}: {description}")
        print(f"  Input:            '{input_str}'")
        print(f"  Expected address: '{expected_address}'")
        print(f"  Actual address:   '{from_address}'")
        print(f"  Expected name:    '{expected_name}'")
        print(f"  Actual name:      '{from_name}'")
        print(f"  Status:           {status}")

        if not address_match:
            print(f"  ⚠ Address mismatch!")
        if not name_match:
            print(f"  ⚠ Name mismatch!")

    print("\n" + "=" * 80)
    print(f"\nTest Results: {passed} passed, {failed} failed out of {len(test_cases)} total")
    print("=" * 80)

    return failed == 0


if __name__ == "__main__":
    success = test_parsing()
    exit(0 if success else 1)
