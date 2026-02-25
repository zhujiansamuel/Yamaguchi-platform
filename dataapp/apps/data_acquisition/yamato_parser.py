"""
Yamato tracking HTML parser for extracting delivery information.
"""
from lxml import etree
from datetime import datetime
import re


def extract_tracking_data(html_content: str, year: int = 2026):
    """
    Extract tracking data from Yamato tracking HTML response.

    Args:
        html_content: HTML content string from Yamato tracking response
        year: Year to use for date parsing (default: 2026)

    Returns:
        list: List of dictionaries with tracking information:
            [
                {
                    'tracking_number': str,  # 12-digit tracking number or None
                    'delivery_date': datetime.date,  # Delivery date or None
                    'delivery_status': str,  # Delivery status in Japanese or None
                },
                ...
            ]

    Example:
        >>> html = "<html>...</html>"
        >>> results = extract_tracking_data(html)
        >>> print(results)
        [
            {
                'tracking_number': '483655383050',
                'delivery_date': datetime.date(2026, 1, 13),
                'delivery_status': '配達完了'
            },
            ...
        ]
    """
    parser = etree.HTMLParser()
    tree = etree.fromstring(html_content, parser)
    results = []

    # Find all tracking box areas
    rows = tree.xpath("//div[contains(@class,'tracking-box-area')]")

    for row in rows:
        # Extract tracking number
        value = "".join(
            row.xpath(".//div[contains(@class,'data') and contains(@class,'number')]//input/@value")
        ).strip()
        digits = re.sub(r"\D", "", value)
        tracking_number = digits if len(digits) >= 12 else None

        # Extract delivery date
        date_text = "".join(
            row.xpath(".//div[contains(@class,'data') and contains(@class,'date') and contains(@class,'pc-only')]/text()")
        ).strip()
        delivery_date = None
        if date_text:
            try:
                delivery_date = datetime.strptime(f"{year}/{date_text}", "%Y/%m/%d").date()
            except ValueError:
                delivery_date = None

        # Extract delivery status
        a = row.xpath(".//div[contains(@class,'data') and contains(@class,'state')]//a")
        delivery_status = None
        if a:
            full_text = "".join(a[0].itertext())
            full_text = re.sub(r"\s+", " ", full_text).strip()
            full_text = re.sub(r"\b\d{2}/\d{2}\b", "", full_text).strip()
            full_text = full_text.replace("▶", "").strip()
            delivery_status = full_text or None

        # Add result if any field has data
        if tracking_number or delivery_date or delivery_status:
            results.append({
                "tracking_number": tracking_number,
                "delivery_date": delivery_date,
                "delivery_status": delivery_status,
            })

    return results
