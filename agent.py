import os
import smtplib
import traceback
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from playwright.sync_api import sync_playwright

TARGET_URL = "https://gfiber.com/webpass/signup/"

LOCATIONS = [
    {
        "address": "18 10th Street San Francisco CA 94103",
        "unit": "224",
        "prefix": "sf",
        "label": "San Francisco"
    },
    {
        "address": "501 Roy Street Seattle WA 98109",
        "unit": "216",
        "prefix": "sea",
        "label": "Seattle"
    }
]

DEFAULT_SENDER = "lestar72@gmail.com"
DEFAULT_RECIPIENTS = "rgalvin@gfiber.com, lestar72@gmail.com"

def run_agent():
    print("=== STARTING AGENT RUN ===")
    captured_screenshots = []
    email_body_text = "GFiber Webpass 3-Day Appointment Schedule Report\n\n"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--window-size=1440,900"
            ]
        )

        for loc in LOCATIONS:
            print(f"\n--- Processing Location: {loc['label']} ({loc['address']} #{loc['unit']}) ---")
            email_body_text += f"Location: {loc['address']} #{loc['unit']}\n"
            
            context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            try:
                print(f"Navigating to {TARGET_URL}...")
                # Changed from networkidle to domcontentloaded to prevent cloud timeouts
                page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(5000)

                # Step 1: Type Address
                print(f"Targeting visible address input and typing {loc['address']}...")
                address_input = page.get_by_placeholder("Enter your address").locator("visible=true").first
                address_input.click(force=True)
                page.wait_for_timeout(1000)
                
                address_main = loc['address'][:-1]
                address_last = loc['address'][-1]
                
                address_input.press_sequentially(address_main, delay=150)
                page.wait_for_timeout(2000)
                address_input.press_sequentially(address_last, delay=200)
                page.wait_for_timeout(4000)

                # Step 2: Select Google Places Item
                print("Clicking the Google Places dropdown...")
                pac_item = page.locator(".pac-container .pac-item").first
                if pac_item.is_visible(timeout=5000):
                    pac_item.click(force=True)
                else:
                    address_input.press("ArrowDown")
                    page.wait_for_timeout(1000)
                    address_input.press("Enter")
                
                page.wait_for_timeout(4000)

                # Step 3: Select Unit
                print(f"Clicking Unit field and selecting {loc['unit']}...")
                unit_field = page.locator("input[placeholder*='Unit' i], select[name*='unit' i], input[name*='unit' i]").locator("visible=true").first
                if unit_field.is_visible(timeout=5000):
                    unit_field.click(force=True)
                    page.wait_for_timeout(1000)
                    
                    if unit_field.evaluate("el => el.tagName.toLowerCase() === 'select'"):
                        try:
                            unit_field.select_option(label=loc['unit'])
                        except:
                            unit_field.select_option(value=loc['unit'])
                    else:
                        unit_field.press_sequentially(loc['unit'], delay=200)
                        page.wait_for_timeout(1500)
                        page.keyboard.press("ArrowDown")
                        page.wait_for_timeout(500)
                        page.keyboard.press("Enter")

                page.wait_for_timeout(3000)

                # Step 4: Click Check Availability
                print("Clicking 'Check availability'...")
                check_button = page.locator("button:has-text('Check availability'), button:has-text('Check Availability')").locator("visible=true").first
                if check_button.is_visible(timeout=5000):
                    check_button.click(force=True)
                else:
                    page.keyboard.press("Enter")
                
                page.wait_for_timeout(8000)

                # Step 5: Click through intermediary screens
                print("Clicking through intermediary screens...")
                for i in range(5):
                    next_btn = page.locator("button:has-text('Next'), button:has-text('Continue'), button:has-text('Confirm'), button:has-text('Verify')").locator("visible=true").first
                    if next_btn.is_visible(timeout=5000):
                        print(f"Clicking intermediary button (Screen {i+1})...")
                        next_btn.click(force=True)
                        page.wait_for_timeout(6000)
                    
                    calendar_check = page.locator("text='Select a date and time', [role='tab']")
                    if calendar_check.count() > 0 and calendar_check.first.is_visible():
                        print("Successfully reached the appointment calendar!")
                        break

                page.wait_for_timeout(
