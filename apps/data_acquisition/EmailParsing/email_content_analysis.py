"""
Worker for analyzing email content and distributing to appropriate handlers.

Queue: email_content_analysis_queue
Redis DB: 10

This worker:
1. Reads emails from database
2. Analyzes content to determine email type
3. Creates appropriate tasks for the three email handlers
"""

import logging
import re
from typing import Optional, Dict, Any, List
from lxml import html

logger = logging.getLogger(__name__)


# ========== 辅助函数 ==========

def _norm(s: str) -> str:
    """规范化字符串：去除多余空白"""
    return " ".join((s or "").split()).strip()


def _parse_qty_from_text(text: str) -> Optional[int]:
    """从文本中提取数量（一位数字）"""
    m = re.search(r"数量\s*(\d)", text or "")
    return int(m.group(1)) if m else None


def _dates_from_text(text: str) -> Optional[Dict[str, str]]:
    """从文本中提取日期（支持单日期和日期区间）"""
    dates = re.findall(r"\d{4}/\d{2}/\d{2}", text or "")
    if not dates:
        return None
    if len(dates) == 1:
        return {"type": "single", "date": dates[0]}
    # 取前两个，表示 range
    return {"type": "range", "start_date": dates[0], "end_date": dates[1]}


def _pick_first_product_name(elements: List[Any]) -> Optional[str]:
    """
    在一个"分组片段"里挑最可能的商品名：
    1) 优先 class='product-name-td'
    2) 否则挑 style 里含 font-weight:600 的 td，但排除价格(含'円')、排除字段标题类文本
    """
    # 1) explicit class
    for e in elements:
        if getattr(e, "tag", None) == "td" and "product-name-td" in (e.get("class") or ""):
            name = _norm(e.text_content())
            if name:
                return name

    # 2) heuristic
    blacklist = (
        "お届け予定日", "ご注文番号", "ご注文日", "配送先住所", "お届け連絡先",
        "配達伝票番号", "配送業者名", "合計", "小計", "税込", "円"
    )
    for e in elements:
        if getattr(e, "tag", None) != "td":
            continue
        style = e.get("style") or ""
        if "font-weight:600" not in style.replace(" ", "") and "font-weight:600" not in style:
            continue
        text = _norm(e.text_content())
        if not text:
            continue
        if any(b in text for b in blacklist):
            continue
        # 很短的"标题类"也排除一下
        if len(text) < 6:
            continue
        return text

    return None


def _pick_first_quantity(elements: List[Any]) -> Optional[int]:
    """从元素列表中提取第一个数量值"""
    # 优先找 nobr '数量 N'
    for e in elements:
        if getattr(e, "tag", None) == "nobr":
            t = _norm(e.text_content())
            q = _parse_qty_from_text(t)
            if q is not None:
                return q
    # 回退：扫所有文本
    for e in elements:
        if not hasattr(e, "text_content"):
            continue
        q = _parse_qty_from_text(_norm(e.text_content()))
        if q is not None:
            return q
    return None


def extract_line_items_from_order_email(tree) -> List[Dict[str, Any]]:
    """
    从订单确认邮件中提取商品列表
    兼容两类模板：
    A) 分组：お届け予定日 1 / お届け予定日 2 ...（每组一个商品+一个预计到达时间）
    B) 非分组：一个お届け予定日 + 一个或多个商品
    """
    root = tree.getroottree().getroot()

    # A) 找"お届け予定日 N"标题（用正则匹配）
    headings = root.xpath(
        "//div[starts-with(normalize-space(.),'お届け予定日 ')]"
    )
    # 过滤出真正的"お届け予定日 数字"标题
    headings = [h for h in headings if re.match(r"お届け予定日 \d+", _norm(h.text_content()))]

    # 建立文档顺序索引，便于切分片段
    all_elems = list(root.iter())
    idx = {e: i for i, e in enumerate(all_elems)}

    items: List[Dict[str, Any]] = []

    if headings:
        # 分组模板
        for i, h in enumerate(headings):
            start_i = idx.get(h, 0)
            end_i = idx.get(headings[i + 1], len(all_elems)) if i + 1 < len(headings) else len(all_elems)
            segment = all_elems[start_i:end_i]

            # 该组的日期文本在标题 div 的下一个 sibling div
            date_div = h.xpath("following-sibling::div[1]")
            delivery = _dates_from_text(_norm(date_div[0].text_content())) if date_div else None

            product_name = _pick_first_product_name(segment)
            qty = _pick_first_quantity(segment)

            items.append({
                "product_name": product_name,
                "quantity": qty,
                "delivery": delivery,
            })
        return items

    # B) 非分组：取全局"お届け予定日 ..."
    delivery_text_nodes = root.xpath(
        "//span[contains(normalize-space(.),'お届け予定日')]/text()"
    )
    delivery = _dates_from_text(_norm(delivery_text_nodes[0])) if delivery_text_nodes else None

    # 商品名：优先 product-name-td
    name_nodes = root.xpath("//td[contains(@class,'product-name-td')]")
    if name_nodes:
        names = [_norm(n.text_content()) for n in name_nodes if _norm(n.text_content())]
    else:
        names = []

    # 数量：找所有 nobr 包含"数量"的
    qty_nodes = root.xpath("//nobr[contains(normalize-space(.),'数量')]/text()")
    quantities = [_parse_qty_from_text(_norm(q)) for q in qty_nodes]
    quantities = [q for q in quantities if q is not None]

    # 如果只有一个数量，所有商品共享
    if len(quantities) == 1:
        quantities = [quantities[0]] * len(names)
    elif len(quantities) == 0:
        quantities = [None] * len(names)

    # 组合成商品列表
    for i, name in enumerate(names):
        qty = quantities[i] if i < len(quantities) else None
        items.append({
            "product_name": name,
            "quantity": qty,
            "delivery": delivery,
        })

    return items if items else []


# ========== 原有辅助函数 ==========

def xpath_str(tree: html.HtmlElement, expr: str, default: str = "") -> str:
    """
    对于返回 string 的 XPath 表达式：直接拿到字符串；
    对于返回 list 的表达式：取第一个元素并转为字符串。
    """
    res = tree.xpath(expr)
    if isinstance(res, list):
        if not res:
            return default
        v = res[0]
        # v 可能是 element，也可能是 str/bytes/数字
        if hasattr(v, "text_content"):
            return v.text_content().strip()
        return str(v).strip()
    if res is None:
        return default
    return str(res).strip()


def first_group(text: str, pattern: str) -> Optional[str]:
    """提取正则表达式的第一个分组"""
    m = re.search(pattern, text)
    return m.group(1) if m else None


def extract_fields_from_html(html_text: str) -> Dict[str, Any]:
    """
    解析配送通知邮件的HTML内容，提取订单和配送信息

    Args:
        html_text: HTML内容字符串

    Returns:
        包含提取信息的字典
    """
    tree = html.fromstring(html_text)

    # ご注文番号（文本+链接）
    order_number_value = xpath_str(
        tree,
        "normalize-space(string(//span[normalize-space()='ご注文番号:']/following-sibling::span//a))",
        default="",
    ) or None
    order_number_href = xpath_str(
        tree,
        "string(//span[normalize-space()='ご注文番号:']/following-sibling::span//a/@href)",
        default="",
    ) or None

    # ご注文日（文本）
    order_date = xpath_str(
        tree,
        "normalize-space(string(//span[normalize-space()='ご注文日:']/following-sibling::span[1]))",
        default="",
    ) or None

    # お届け予定日（全局）
    delivery_blob = xpath_str(
        tree,
        "normalize-space(string(//span[contains(normalize-space(.),'お届け予定日')]))",
        default="",
    )
    delivery_date_str = first_group(delivery_blob, r"(\d{4}/\d{2}/\d{2})")
    delivery_dict = None
    if delivery_date_str:
        delivery_dict = {"type": "single", "date": delivery_date_str}

    # ========== 商品列表（新增：支持多商品）==========
    # 提取所有商品名
    product_name_nodes = tree.xpath("//td[contains(@class,'product-name-td')]")
    product_names = [_norm(n.text_content()) for n in product_name_nodes if _norm(n.text_content())]

    # 提取所有数量
    qty_nodes = tree.xpath("//nobr[contains(normalize-space(.),'数量')]/text()")
    quantities = [_parse_qty_from_text(_norm(q)) for q in qty_nodes]
    quantities = [q for q in quantities if q is not None]

    # 如果只有一个数量，所有商品共享
    if len(quantities) == 1 and len(product_names) > 1:
        quantities = [quantities[0]] * len(product_names)
    elif len(quantities) == 0:
        quantities = [None] * len(product_names)

    # 组合成商品列表
    line_items = []
    for i, name in enumerate(product_names):
        qty = quantities[i] if i < len(quantities) else None
        line_items.append({
            "product_name": name,
            "quantity": qty,
            "delivery": delivery_dict,
        })

    # ========== 向后兼容字段（从第一个商品提取）==========
    if line_items and len(line_items) > 0:
        first_item = line_items[0]
        iphone_product_names = first_item.get('product_name')
        quantity = first_item.get('quantity')
    else:
        # 回退到原有逻辑
        iphone_product_names = xpath_str(
            tree,
            "normalize-space(string(//td[contains(@class,'product-name-td')]))",
            default="",
        ) or None
        qty_blob = xpath_str(
            tree,
            "normalize-space(string(//nobr[contains(normalize-space(.),'数量')]))",
            default="",
        )
        quantity = _parse_qty_from_text(qty_blob)

    # 配送先住所（多行 div）
    addr_lines: List[str] = [
        s.strip()
        for s in tree.xpath(
            "//h3[contains(normalize-space(.),'配送先住所')]/following-sibling::div[contains(@class,'gen-txt')][1]/div/text()"
        )
        if s and s.strip()
    ]
    postal_code = addr_lines[0] if len(addr_lines) > 0 else None
    prefecture_city = addr_lines[1] if len(addr_lines) > 1 else None
    street_address = addr_lines[2] if len(addr_lines) > 2 else None
    name_line = addr_lines[3] if len(addr_lines) > 3 else None
    recipient_name = re.sub(r"様\s*$", "", name_line).strip() if name_line else None

    # お届け連絡先（邮箱）
    contact_email = xpath_str(
        tree,
        "normalize-space(string(//h3[contains(normalize-space(.),'お届け連絡先')]/following-sibling::div[1]//span[contains(@class,'moe-break-me')]))",
        default="",
    ) or None

    # 配達伝票番号（文本+链接）
    tracking_number = xpath_str(
        tree,
        "normalize-space(string(//h3[contains(normalize-space(.),'配達伝票番号')]/following-sibling::div[1]//a))",
        default="",
    ) or None
    tracking_href = xpath_str(
        tree,
        "string(//h3[contains(normalize-space(.),'配達伝票番号')]/following-sibling::div[1]//a/@href)",
        default="",
    ) or None

    # 配送業者名
    carrier_name = xpath_str(
        tree,
        "normalize-space(string(//h3[contains(normalize-space(.),'配送業者名')]/following-sibling::div[contains(@class,'gen-txt-carrier')][1]))",
        default="",
    ) or None

    return {
        "order_number": order_number_value,
        "official_query_url": order_number_href,
        "confirmed_at": order_date,
        "estimated_website_arrival_date": delivery_date_str,
        "line_items": line_items,
        "iphone_product_names": iphone_product_names,
        "quantity": quantity,
        "postal_code": postal_code,
        "address_line_1": prefecture_city,
        "address_line_2": street_address,
        "name": recipient_name,
        "email": contact_email,
        "tracking_number": tracking_number,
        "tracking_href": tracking_href,
        "carrier_name": carrier_name,
    }


def extract_delivery_dates(tree) -> Optional[Dict[str, Any]]:
    """
    支持两种格式的配送日期提取（区间 / 单日），并兼容日期在文本节点或子标签内

    Args:
        tree: lxml HTML tree

    Returns:
        Dictionary containing delivery date information or None if not found
    """
    # 只匹配带冒号的那一个（避免误匹配上面"お届け予定日 1"的标题）
    spans = tree.xpath(
        "//span[contains(normalize-space(.), 'お届け予定日') and (contains(., '：') or contains(., ':'))]"
    )
    if not spans:
        return None

    span = spans[0]
    container = span.getparent()  # <span> 所在的父节点，通常就是那个包着日期的 <div>

    # 抓取容器内的全部文本（包含子元素内文本），避免日期被包在其他标签里导致漏抓
    raw_text = "".join(container.xpath(".//text()"))
    normalized = re.sub(r"\s+", " ", raw_text).strip()

    # 只从"お届け予定日："之后开始提取日期，避免容器内其他位置存在日期时误抓
    m = re.search(r"お届け予定日\s*[:：]\s*", normalized)
    target_text = normalized[m.end():] if m else normalized

    dates = re.findall(r"\d{4}/\d{2}/\d{2}", target_text)
    if not dates:
        return None

    if len(dates) >= 2:
        return {
            "type": "range",
            "start_date": dates[0],
            "end_date": dates[1],
            "full_text": f"{dates[0]} - {dates[1]}",
        }

    return {
        "type": "single",
        "date": dates[0],
        "full_text": dates[0],
    }


def parse_apple_order_email(html_content: str) -> Optional[Dict[str, Any]]:
    """
    解析Apple订单确认邮件的HTML内容，提取订单信息

    Args:
        html_content: HTML内容字符串

    Returns:
        包含提取信息的字典，如果解析失败则返回None
    """
    try:
        tree = html.fromstring(html_content)
    except Exception as e:
        logger.error(f"Failed to parse HTML content: {e}")
        return None

    result = {}

    # ========== 订单号（文本+链接）==========
    official_query_urls = tree.xpath("//a[@class='aapl-link' and contains(@href, 'vieworder')]")
    if official_query_urls:
        official_query_url_elem = official_query_urls[0]
        result['official_query_url'] = (
            official_query_url_elem.xpath('./@href')[0]
            if official_query_url_elem.xpath('./@href')
            else ''
        )
        order_number_text = (
            official_query_url_elem.xpath('./text()')[0]
            if official_query_url_elem.xpath('./text()')
            else ''
        )
        result['order_number'] = order_number_text
    else:
        result['official_query_url'] = None
        result['order_number'] = None

    # ========== 订单日期 ==========
    order_dates = tree.xpath("//div[@class='order-num']//span[contains(text(), '/')]/text()")
    result['confirmed_at'] = order_dates[0] if order_dates else None

    # ========== 商品列表（新增：支持多商品）==========
    line_items = extract_line_items_from_order_email(tree)
    result['line_items'] = line_items

    # ========== 向后兼容字段（从第一个商品提取）==========
    if line_items and len(line_items) > 0:
        first_item = line_items[0]
        result['iphone_product_names'] = first_item.get('product_name')
        result['quantities'] = first_item.get('quantity')

        # 配送日期从第一个商品提取
        delivery = first_item.get('delivery')
        if delivery:
            if delivery.get('type') == 'range':
                result['estimated_website_arrival_date'] = delivery.get('start_date')
                result['estimated_website_arrival_date_2'] = delivery.get('end_date')
            else:
                result['estimated_website_arrival_date'] = delivery.get('date')
                result['estimated_website_arrival_date_2'] = None
        else:
            result['estimated_website_arrival_date'] = None
            result['estimated_website_arrival_date_2'] = None
    else:
        # 如果没有提取到商品，使用原有逻辑作为后备
        product_names = tree.xpath("//td[@class='product-name-td']//text()")
        result['iphone_product_names'] = product_names[0].strip() if product_names else None

        # 数量：使用新的正则提取逻辑
        qty_text_nodes = tree.xpath("//nobr[contains(normalize-space(.),'数量')]/text()")
        if qty_text_nodes:
            result['quantities'] = _parse_qty_from_text(_norm(qty_text_nodes[0]))
        else:
            result['quantities'] = None

        # 配送日期
        delivery_info = extract_delivery_dates(tree)
        if delivery_info:
            if delivery_info['type'] == 'range':
                result['estimated_website_arrival_date'] = delivery_info['start_date']
                result['estimated_website_arrival_date_2'] = delivery_info['end_date']
            else:
                result['estimated_website_arrival_date'] = delivery_info['date']
                result['estimated_website_arrival_date_2'] = None
        else:
            result['estimated_website_arrival_date'] = None
            result['estimated_website_arrival_date_2'] = None

    # ========== 配送地址 ==========
    address_elements = tree.xpath("//h3[contains(text(), 'お届け先住所')]/following-sibling::div[@class='gen-txt']/text()")
    if len(address_elements) >= 4:
        result['name'] = address_elements[3].strip()
        result['postal_code'] = address_elements[0].strip()
        result['address_line_1'] = address_elements[1].strip()
        result['address_line_2'] = address_elements[2].strip()
    else:
        result['name'] = None
        result['postal_code'] = None
        result['address_line_1'] = None
        result['address_line_2'] = None

    # ========== 邮箱 ==========
    emails = tree.xpath("//div[contains(., '@')]/text()")
    email = None
    for e in emails:
        if '@' in e:
            email = e.strip()
            break
    result['email'] = email

    return result


class EmailContentAnalysisWorker:
    """
    Worker for analyzing email content and routing to appropriate handlers.
    
    This worker processes emails from the database and determines which
    handler should process each email based on content analysis.
    """

    QUEUE_NAME = 'email_content_analysis_queue'
    WORKER_NAME = 'email_content_analysis_worker'

    def __init__(self):
        """Initialize the email content analysis worker."""
        pass

    def link_official_account(self, mail_account, recipient_email: str, recipient_name: str = '') -> None:
        """
        查询或创建 OfficialAccount，并与 MailAccount 建立关联。

        Args:
            mail_account: MailAccount 实例
            recipient_email: 收件人邮箱地址（从邮件解析出）
            recipient_name: 收件人姓名（可选，从邮件解析出）
        """
        from apps.data_aggregation.models import OfficialAccount

        if not recipient_email:
            logger.warning(f"[{self.WORKER_NAME}] No recipient email provided for linking")
            return

        # 如果 MailAccount 已经关联了 OfficialAccount，则不再处理
        if mail_account.official_account:
            logger.info(
                f"[{self.WORKER_NAME}] MailAccount {mail_account.email_address} "
                f"already linked to OfficialAccount {mail_account.official_account.email}"
            )
            return

        # 查询或创建 OfficialAccount
        official_account, created = OfficialAccount.objects.get_or_create(
            email=recipient_email,
            defaults={
                'account_id': recipient_email.split('@')[0],  # 使用邮箱前缀作为 account_id
                'passkey': '111111',  # 默认 passkey
                'name': recipient_name or '',
            }
        )

        # 建立关联
        mail_account.official_account = official_account
        mail_account.save()

        if created:
            logger.info(
                f"[{self.WORKER_NAME}] Created new OfficialAccount: {recipient_email} "
                f"and linked to MailAccount {mail_account.email_address}"
            )
        else:
            logger.info(
                f"[{self.WORKER_NAME}] Linked existing OfficialAccount: {recipient_email} "
                f"to MailAccount {mail_account.email_address}"
            )

    def fetch_emails_from_database(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch unprocessed emails from the database.

        Args:
            limit: Maximum number of emails to fetch (default: 10)

        Returns:
            List of dictionaries containing email data
        """
        from apps.data_aggregation.models import MailMessage

        try:
            # 查询未提取过的邮件，按时间从旧到新排序，取limit封
            mails = (
                MailMessage.objects
                .exclude(is_extracted=True)
                .filter(body__isnull=False)
                .select_related('body', 'account')
                .order_by('date_header_at')[:limit]
            )

            if not mails:
                return []

            # 构建返回的列表
            result = []
            for mail in mails:
                result.append({
                    'id': mail.id,
                    'subject': mail.subject,
                    'from_address': mail.from_address,
                    'from_name': mail.from_name,
                    'date_header_at': mail.date_header_at,
                    'html_content': mail.body.text_html if hasattr(mail, 'body') else '',
                    'account': mail.account,  # 添加 account 对象
                })

            return result

        except Exception as e:
            logger.error(f"[{self.WORKER_NAME}] Error fetching emails: {e}", exc_info=True)
            return []

    def analyze_email_content(self, email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze email content and extract Apple order information.

        Args:
            email_data: Dictionary containing email information

        Returns:
            Dictionary containing extracted order information or None if parsing fails
        """
        logger.info(
            f"[{self.WORKER_NAME}] Analyzing email content for email_id={email_data.get('id')}"
        )

        html_content = email_data.get('html_content', '')
        if not html_content:
            logger.warning(f"[{self.WORKER_NAME}] No HTML content found in email")
            return None

        # 使用parse_apple_order_email函数解析HTML
        parsed_data = parse_apple_order_email(html_content)

        if parsed_data is None:
            logger.error(f"[{self.WORKER_NAME}] Failed to parse Apple order email")
            return None

        # 添加邮件的元数据到解析结果中
        parsed_data['email_id'] = email_data.get('id')
        parsed_data['email_subject'] = email_data.get('subject')
        parsed_data['email_date'] = email_data.get('date_header_at')

        logger.info(
            f"[{self.WORKER_NAME}] Successfully parsed email, "
            f"order_number={parsed_data.get('order_number')}"
        )

        return parsed_data

    def create_handler_task(self, email_type: str, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a task for the appropriate email handler.
        
        Args:
            email_type: Type of email ('initial_order_confirmation', etc.)
            email_data: Email data to pass to the handler
            
        Returns:
            Dictionary containing task creation result
            
        TODO: Import and call the appropriate task
        - Import task functions from tasks_* modules
        - Call .delay() to queue the task
        - Return task ID and status
        """
        logger.info(
            f"[{self.WORKER_NAME}] Creating {email_type} task with email_id={email_data.get('id')} (TODO)"
        )
        
        # Placeholder
        return {
            'status': 'queued',
            'email_type': email_type,
            'email_id': email_data.get('id'),
        }

    def execute(self, task_data: dict) -> dict:
        """
        Execute the email content analysis.

        Fetches up to 10 unprocessed emails, marks them as extracted, classifies them, and triggers appropriate tasks.

        Args:
            task_data: Dictionary containing task parameters

        Returns:
            Dictionary containing execution results
        """
        from apps.data_aggregation.models import MailMessage
        from apps.data_acquisition.EmailParsing.tasks_initial_order_confirmation_email import (
            process_email as process_initial_order,
        )
        from apps.data_acquisition.EmailParsing.tasks_send_notification_email import (
            process_email as process_shipping_notification,
        )

        try:
            # Fetch up to 10 emails
            emails = self.fetch_emails_from_database(limit=10)

            if not emails:
                return {
                    'status': 'no_email',
                    'message': 'No unprocessed emails found',
                    'processed_count': 0,
                }

            # Mark all fetched emails as extracted immediately
            email_ids = [email.get('id') for email in emails]
            MailMessage.objects.filter(id__in=email_ids).update(is_extracted=True)

            processed_emails = []
            skipped_emails = []

            # Process each email
            for email_data in emails:
                email_id = email_data.get('id')
                subject = email_data.get('subject', '')
                from_address = email_data.get('from_address', '')
                html_content = email_data.get('html_content', '')

                # Classify email type and process accordingly
                email_type = None
                extracted_data = None
                task_id = None

                # Type 1: Initial Order Confirmation
                if (
                    "ご注文ありがとうございます" in subject
                    and from_address == "order_acknowledgment@orders.apple.com"
                    and html_content
                ):
                    email_type = 'initial_order_confirmation'
                    try:
                        extracted_data = parse_apple_order_email(html_content)
                        if extracted_data:
                            extracted_data['email_id'] = email_id
                            extracted_data['email_subject'] = subject
                            extracted_data['email_date'] = email_data.get('date_header_at')

                            # 关联 OfficialAccount
                            recipient_email = extracted_data.get('email')
                            recipient_name = extracted_data.get('name', '')
                            mail_account = email_data.get('account')
                            if recipient_email and mail_account:
                                self.link_official_account(mail_account, recipient_email, recipient_name)

                            task_result = process_initial_order.delay(email_data=extracted_data)
                            task_id = task_result.id
                    except Exception as e:
                        logger.error(f"[{self.WORKER_NAME}] Parse error email_id={email_id}: {e}")

                # Type 2: Shipping Notification
                elif (
                    "お客様の商品は配送中です" in subject
                    and from_address == "shipping_notification_jp@orders.apple.com"
                    and html_content
                ):
                    email_type = 'shipping_notification'
                    try:
                        extracted_data = extract_fields_from_html(html_content)
                        if extracted_data:
                            extracted_data['email_id'] = email_id
                            extracted_data['email_subject'] = subject
                            extracted_data['email_date'] = email_data.get('date_header_at')

                            # 关联 OfficialAccount
                            recipient_email = extracted_data.get('email')
                            recipient_name = extracted_data.get('name', '')
                            mail_account = email_data.get('account')
                            if recipient_email and mail_account:
                                self.link_official_account(mail_account, recipient_email, recipient_name)

                            task_result = process_shipping_notification.delay(email_data=extracted_data)
                            task_id = task_result.id
                    except Exception as e:
                        logger.error(f"[{self.WORKER_NAME}] Parse error email_id={email_id}: {e}")

                # Record processing result
                if extracted_data and task_id:
                    processed_emails.append({
                        'email_id': email_id,
                        'type': email_type,
                        'task_id': task_id,
                        'order_number': extracted_data.get('order_number'),
                    })
                else:
                    # Email doesn't match any criteria or parsing failed
                    skipped_emails.append({
                        'email_id': email_id,
                        'subject': subject[:50],
                        'from': from_address,
                    })

            return {
                'status': 'success',
                'processed_count': len(processed_emails),
                'skipped_count': len(skipped_emails),
                'processed_emails': processed_emails,
                'message': f'Processed {len(processed_emails)} emails, skipped {len(skipped_emails)}',
            }

        except Exception as e:
            logger.error(f"[{self.WORKER_NAME}] Error: {e}", exc_info=True)
            raise

    def run(self, task_data: dict) -> dict:
        """
        Run the worker with proper error handling.

        Args:
            task_data: Dictionary containing task parameters

        Returns:
            Dictionary containing execution results
        """
        try:
            logger.info(f"[{self.WORKER_NAME}] Starting task with data: {task_data}")
            result = self.execute(task_data)

            # Log task statistics
            logger.info(f"[{self.WORKER_NAME}] ===== Task Statistics =====")
            if result.get('status') == 'success':
                processed_count = result.get('processed_count', 0)
                skipped_count = result.get('skipped_count', 0)
                processed_emails = result.get('processed_emails', [])

                logger.info(f"[{self.WORKER_NAME}] Total processed: {processed_count}")
                logger.info(f"[{self.WORKER_NAME}] Total skipped: {skipped_count}")

                if processed_emails:
                    logger.info(f"[{self.WORKER_NAME}] --- Processed Emails ---")
                    for email in processed_emails:
                        logger.info(
                            f"[{self.WORKER_NAME}]   Email ID: {email.get('email_id')}, "
                            f"Type: {email.get('type')}, "
                            f"Order: {email.get('order_number')}, "
                            f"Task: {email.get('task_id')}"
                        )
            elif result.get('status') == 'no_email':
                logger.info(f"[{self.WORKER_NAME}] No unprocessed emails found")
            else:
                logger.info(f"[{self.WORKER_NAME}] Status: {result.get('status')}")

            logger.info(f"[{self.WORKER_NAME}] ==============================")
            logger.info(f"[{self.WORKER_NAME}] Task completed successfully")

            return {
                'status': 'success',
                'result': result,
            }
        except Exception as e:
            logger.error(f"[{self.WORKER_NAME}] Task failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
            }
