"""
Celery tasks for Apple Store pickup contact updates using Playwright.

This module provides browser automation to update pickup contact information
on Apple Store orders.
"""

import asyncio
import logging
import os
import random
import re
import time
from datetime import datetime
from pathlib import Path

from celery import shared_task

logger = logging.getLogger(__name__)

# Constants
APPLE_HOME = "https://www.apple.com/jp/"
DEBUG_DIR = "/app/logs/playwright_debug"

# Element IDs (template - will be formatted with order item ID)
BTN_UPDATE_PICKUP_TEMPLATE = "orderDetail.orderItems.orderItem-{item_id}.shippingInfo.updatePickupContact"
INP_LASTNAME_TEMPLATE = "orderDetail.orderItems.orderItem-{item_id}.shippingInfo.updateThirdPartyPickupInfo.update-pickup-contact.lastName"
INP_FIRSTNAME_TEMPLATE = "orderDetail.orderItems.orderItem-{item_id}.shippingInfo.updateThirdPartyPickupInfo.update-pickup-contact.firstName"
BTN_SUBMIT_TEMPLATE = "orderDetail.orderItems.orderItem-{item_id}.shippingInfo.updateThirdPartyPickupInfo.pickup-contact-submit"

# Default order item ID
DEFAULT_ITEM_ID = "0000101"


def split_name_jp(fullname: str) -> tuple[str, str]:
    """
    Split Japanese full name into last name and first name.

    Args:
        fullname: Full name string (e.g., "山田 太郎")

    Returns:
        Tuple of (last_name, first_name)
    """
    if not isinstance(fullname, str) or not fullname.strip():
        return "", ""
    s = fullname.replace("\u3000", " ")  # Replace full-width space
    s = re.sub(r"\s+", " ", s).strip()
    parts = s.split(" ")
    if len(parts) >= 2:
        return parts[0], parts[1]
    return parts[0], ""


async def maybe_switch_to_popup_or_same_page(context, current_page, click_coro, wait_ms=1200):
    """Check if a new page opened and return it, otherwise return current page."""
    before = len(context.pages)
    await click_coro
    await current_page.wait_for_timeout(wait_ms)
    after = len(context.pages)
    return context.pages[-1] if after > before else current_page


async def open_orders_page(page, context):
    """Navigate to Apple Store orders page."""
    logger.info("Opening orders page...")
    await page.goto(APPLE_HOME, wait_until="domcontentloaded", timeout=30000)
    await page.locator("#globalnav-menubutton-link-bag").wait_for(timeout=10000)
    await page.locator("#globalnav-menubutton-link-bag").click()

    bag_menu = page.locator("#globalnav-submenu-bag")
    orders_link = bag_menu.get_by_role(
        "link",
        name=re.compile(r"(ご注文|注文|Orders|注文状況|ご注文状況)")
    ).first
    await orders_link.wait_for(timeout=15000)

    orders_page = await maybe_switch_to_popup_or_same_page(
        context, page, orders_link.click(), wait_ms=1500
    )
    await orders_page.wait_for_load_state("domcontentloaded", timeout=30000)
    logger.info("Orders page opened successfully")
    return orders_page


async def sign_in(page, apple_id: str, password: str):
    """
    Sign in to Apple Store.

    Note: This always performs a fresh login (no cache).
    """
    logger.info(f"Checking login status for {apple_id}...")
    await page.wait_for_load_state("domcontentloaded", timeout=30000)

    frame_loc = page.frame_locator("iframe").first
    account_field = frame_loc.locator("#account_name_text_field")

    try:
        await account_field.wait_for(timeout=6000)
        logger.info("Login form detected, proceeding with sign in")
    except Exception:
        logger.info("Already logged in (no login form)")
        return

    try:
        logger.info("Entering Apple ID...")
        await account_field.fill(apple_id)
        await frame_loc.locator("#sign-in").click()

        # Random delay to appear more human-like
        await asyncio.sleep(random.randint(1, 5))

        logger.info("Entering password...")
        password_field = frame_loc.locator("#password_text_field")
        await password_field.wait_for(timeout=15000)
        await password_field.fill(password)

        await asyncio.sleep(random.randint(1, 5))
        await frame_loc.locator("#sign-in").click()

        logger.info("Waiting for login to complete...")
        try:
            await page.wait_for_selector("#rs-container", timeout=180000)
            logger.info("Login successful")
        except Exception:
            logger.warning("May need 2FA verification, waiting...")
            await page.wait_for_selector("#rs-container", timeout=120000)
            logger.info("Login successful (after 2FA)")

    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise


async def open_target_order(page, ordernumber: str | None = None, product_fallback: str = "iPhone"):
    """Navigate to the target order page."""
    logger.info(f"Opening order: {ordernumber or '(by product name)'}")
    await page.wait_for_load_state("domcontentloaded", timeout=30000)

    if ordernumber and isinstance(ordernumber, str) and ordernumber.strip():
        on = ordernumber.strip()
        logger.info(f"Searching for order number: {on}")

        # Try finding by link
        try:
            link = page.get_by_role("link", name=re.compile(re.escape(on))).first
            await link.wait_for(timeout=10000)
            await link.click()
            await asyncio.sleep(random.randint(1, 3))
            await page.wait_for_load_state("domcontentloaded", timeout=30000)
            logger.info(f"Found order by link: {on}")
            return
        except Exception:
            pass

        # Try finding by text
        try:
            txt = page.get_by_text(on).first
            await txt.wait_for(timeout=10000)
            await txt.click()
            await page.wait_for_load_state("domcontentloaded", timeout=30000)
            logger.info(f"Found order by text: {on}")
            return
        except Exception:
            pass

        logger.warning(f"Order number not found, falling back to product name")

    # Fallback to product name
    logger.info(f"Using product name: {product_fallback}")
    prod_link = page.get_by_role("link", name=re.compile(re.escape(product_fallback))).first
    await prod_link.wait_for(timeout=15000)
    await prod_link.click()
    await asyncio.sleep(random.randint(1, 3))
    await page.wait_for_load_state("domcontentloaded", timeout=30000)
    logger.info("Order opened successfully")


async def update_pickup_contact(page, new_last: str, new_first: str, item_id: str = DEFAULT_ITEM_ID):
    """
    Update the pickup contact name on the order.

    Args:
        page: Playwright page object
        new_last: New last name (姓)
        new_first: New first name (名)
        item_id: Order item ID for element selectors
    """
    logger.info(f"Updating pickup contact: {new_last} {new_first}")

    # Format element IDs
    btn_update_pickup = BTN_UPDATE_PICKUP_TEMPLATE.format(item_id=item_id)
    inp_lastname = INP_LASTNAME_TEMPLATE.format(item_id=item_id)
    inp_firstname = INP_FIRSTNAME_TEMPLATE.format(item_id=item_id)
    btn_submit = BTN_SUBMIT_TEMPLATE.format(item_id=item_id)

    try:
        await page.wait_for_load_state("networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        # Find and click edit button
        logger.info("Finding edit button...")
        update_btn = page.locator(f"//*[@id='{btn_update_pickup}']")
        await update_btn.wait_for(state="visible", timeout=20000)
        await update_btn.click()
        logger.info("Clicked edit button")

        await page.wait_for_timeout(2000)

        # Fill last name
        logger.info(f"Filling last name: {new_last}")
        last_name_input = page.locator(f"//*[@id='{inp_lastname}']")
        await last_name_input.wait_for(state="visible", timeout=15000)
        await asyncio.sleep(random.randint(1, 5))
        await last_name_input.clear()
        await page.wait_for_timeout(300)
        await last_name_input.type(new_last, delay=50)

        await page.wait_for_timeout(500)

        # Fill first name
        logger.info(f"Filling first name: {new_first}")
        first_name_input = page.locator(f"//*[@id='{inp_firstname}']")
        await first_name_input.wait_for(state="visible", timeout=15000)
        await asyncio.sleep(random.randint(1, 5))
        await first_name_input.clear()
        await page.wait_for_timeout(300)
        await first_name_input.type(new_first, delay=50)

        await page.wait_for_timeout(500)

        # Submit
        logger.info("Submitting changes...")
        submit_btn = page.locator(f"//*[@id='{btn_submit}']")
        await submit_btn.wait_for(state="visible", timeout=15000)
        await asyncio.sleep(random.randint(1, 5))
        await submit_btn.click()

        await page.wait_for_timeout(3000)
        logger.info("Pickup contact updated successfully")

    except Exception as e:
        logger.error(f"Update failed: {e}")
        # Take debug screenshot
        os.makedirs(DEBUG_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"{DEBUG_DIR}/error_{timestamp}.png"
        try:
            await page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"Debug screenshot saved: {screenshot_path}")
        except Exception:
            pass
        raise


async def sign_out(page):
    """Sign out from Apple Store."""
    logger.info("Signing out...")
    try:
        await page.locator("#globalnav-menubutton-link-bag").wait_for(timeout=10000)
        await asyncio.sleep(random.randint(1, 5))
        await page.locator("#globalnav-menubutton-link-bag").click()

        bag_menu = page.locator("#globalnav-submenu-bag")
        signout_link = bag_menu.get_by_role(
            "link",
            name=re.compile(r"(サインアウト|Sign Out|ログアウト)")
        ).first

        try:
            await signout_link.wait_for(timeout=8000)
            await signout_link.click()
            logger.info("Signed out successfully")
        except Exception:
            logger.warning("No sign out option available (non-critical)")
    except Exception as e:
        logger.warning(f"Sign out failed (non-critical): {e}")


async def run_pickup_update(
    apple_id: str,
    password: str,
    newname: str,
    ordernumber: str | None = None,
    product_fallback: str = "iPhone",
    item_id: str = DEFAULT_ITEM_ID,
    headless: bool = True,
) -> dict:
    """
    Main async function to update Apple Store pickup contact.

    Args:
        apple_id: Apple ID email
        password: Apple ID password
        newname: New contact name (full name, e.g., "山田 太郎")
        ordernumber: Order number (optional)
        product_fallback: Product name to search if order number not found
        item_id: Order item ID for element selectors
        headless: Whether to run browser in headless mode

    Returns:
        Dict with success status and message
    """
    from playwright.async_api import async_playwright

    new_last, new_first = split_name_jp(newname)
    if not new_last:
        return {
            "success": False,
            "error": "Could not parse newname - no last name found",
            "apple_id": apple_id,
            "ordernumber": ordernumber,
        }

    logger.info(f"Starting pickup update: {apple_id} | Order: {ordernumber or '(product)'} | Name: {new_last} {new_first}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            slow_mo=80,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ]
        )

        context = await browser.new_context(
            locale="ja-JP",
            viewport={"width": 1280, "height": 840},
        )
        page = await context.new_page()
        page.set_default_timeout(30000)

        try:
            orders_page = await open_orders_page(page, context)
            await sign_in(orders_page, apple_id, password)

            await asyncio.sleep(random.randint(1, 3))
            await open_target_order(orders_page, ordernumber, product_fallback)

            await asyncio.sleep(random.randint(1, 3))
            await update_pickup_contact(orders_page, new_last, new_first, item_id)

            await asyncio.sleep(random.randint(1, 3))
            await sign_out(orders_page)

            logger.info(f"Successfully updated: {apple_id}")
            return {
                "success": True,
                "apple_id": apple_id,
                "ordernumber": ordernumber,
                "new_name": f"{new_last} {new_first}",
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to update {apple_id}: {error_msg}")

            # Take error screenshot
            os.makedirs(DEBUG_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_id = re.sub(r'[^a-zA-Z0-9]+', '_', apple_id)[:30]
            screenshot_path = f"{DEBUG_DIR}/fail_{safe_id}_{timestamp}.png"
            try:
                await page.screenshot(path=screenshot_path, full_page=True)
                logger.info(f"Error screenshot saved: {screenshot_path}")
            except Exception:
                pass

            return {
                "success": False,
                "error": error_msg,
                "apple_id": apple_id,
                "ordernumber": ordernumber,
                "screenshot": screenshot_path,
            }

        finally:
            await context.close()
            await browser.close()


@shared_task(
    bind=True,
    name='apps.data_acquisition.workers.tasks_playwright_apple_pickup.process_apple_pickup_contact_update',
    queue='playwright_apple_pickup_queue',
    max_retries=1,
    default_retry_delay=60,
)
def process_apple_pickup_contact_update(
    self,
    apple_id: str,
    password: str,
    newname: str,
    ordernumber: str | None = None,
    product_fallback: str = "iPhone",
    item_id: str = DEFAULT_ITEM_ID,
) -> dict:
    """
    Celery task to update Apple Store pickup contact.

    Args:
        apple_id: Apple ID email
        password: Apple ID password
        newname: New contact name (full name, e.g., "山田 太郎")
        ordernumber: Order number (optional)
        product_fallback: Product name to search if order number not found
        item_id: Order item ID for element selectors

    Returns:
        Dict with success status and details
    """
    logger.info(f"Task started: process_apple_pickup_contact_update for {apple_id}")

    try:
        # Run the async function
        result = asyncio.run(
            run_pickup_update(
                apple_id=apple_id,
                password=password,
                newname=newname,
                ordernumber=ordernumber,
                product_fallback=product_fallback,
                item_id=item_id,
                headless=True,
            )
        )

        if result["success"]:
            logger.info(f"Task completed successfully: {apple_id}")
        else:
            logger.error(f"Task failed: {apple_id} - {result.get('error')}")

        return result

    except Exception as e:
        logger.exception(f"Task exception: {apple_id}")
        return {
            "success": False,
            "error": str(e),
            "apple_id": apple_id,
            "ordernumber": ordernumber,
        }
