import os
import smtplib
import traceback
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from playwright.sync_api import sync_playwright

TARGET_URL = "https://gfiber.com/webpass/signup/"
TARGET_ADDRESS = "18 10th Street, San Francisco"

DEFAULT_SENDER = "lestar72@gmail.com"
DEFAULT_RECIPIENTS = "rgalvin@gfiber.com, lestar72@gmail.com"

def run_agent():
    print("=== STARTING AGENT RUN ===")
    
    d1 = datetime.now()
    d2 = d1 + timedelta(days=1)
    d3 = d1 + timedelta(days=2)
    dates_list = [d1.strftime("%A, %B %d, %Y"), d2.strftime("%A, %B %d, %Y"), d3.strftime("%A, %B %d, %Y")]
    captured_screenshots = []

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
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Evade basic headless detection
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print(f"Navigating to {TARGET_URL}...")
        try:
            page.goto(TARGET_URL, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(5000)

            # Step 1: Human-like typing
            print("Step 1: Typing address slowly...")
            address_input = page.locator("input[placeholder*='address' i], input[type='text']").first
            address_input.click()
            page.wait_for_timeout(1000)
            
            # Type most of the address
            page.keyboard.type("18 10th Stree", delay=250)
            page.wait_for_timeout(2000)
            
            # Type the last letter to trigger the network request
            page.keyboard.type("t", delay=200)
            page.wait_for_timeout(3000)

            # DEBUG: Take a screenshot to see if the dropdown appeared
            print("Capturing DEBUG screenshot of address input...")
            debug_shot = "debug_address_typing.png"
            page.screenshot(path=debug_shot)
            captured_screenshots.append(("DEBUG - Typing Address", debug_shot))

            # Step 2: Attempt to click dropdown
            print("Step 2: Checking for Google Places dropdown...")
            pac_item = page.locator(".pac-container .pac-item").first
            if pac_item.is_visible(timeout=5000):
                pac_item.click()
                print("Clicked autocomplete suggestion!")
            else:
                print("Dropdown not found, pressing ArrowDown + Enter...")
                page.keyboard.press("ArrowDown")
                page.wait_for_timeout(1000)
                page.keyboard.press("Enter")
            
            page.wait_for_timeout(4000)

            # Step 3: Fill Unit 224
            print("Step 3: Selecting Unit 224...")
            unit_field = page.locator("input[placeholder*='Unit' i], input[name*='unit' i], select[name*='unit' i], [id*='unit' i]").first
            if unit_field.is_visible(timeout=5000):
                unit_field.click()
                page.wait_for_timeout(1000)
                if unit_field.evaluate("el => el.tagName.toLowerCase() === 'select'"):
                    try:
                        unit_field.select_option(label="224")
                    except:
                        unit_field.select_option(value="224")
                else:
                    page.keyboard.type("224", delay=200)
                    page.wait_for_timeout(1000)
                    page.keyboard.press("ArrowDown")
                    page.wait_for_timeout(500)
                    page.keyboard.press("Enter")

            page.wait_for_timeout(3000)

            # Step 4: Click Check Availability
            print("Step 4: Clicking 'Check availability'...")
            check_button = page.locator("button:has-text('Check availability'), button:has-text('Check Availability')").first
            if check_button.is_visible(timeout=5000):
                check_button.click()
            else:
                page.keyboard.press("Enter")
            page.wait_for_timeout(8000)

            # DEBUG: Take a screenshot after clicking check availability
            print("Capturing DEBUG screenshot after submit...")
            debug_shot_2 = "debug_after_submit.png"
            page.screenshot(path=debug_shot_2)
            captured_screenshots.append(("DEBUG - After Submit", debug_shot_2))

            # Step 5 & 6: Next Buttons
            next_btn_locator = page.locator("button:has-text('Next'), a:has-text('Next')")
            if next_btn_locator.first.is_visible(timeout=5000):
                next_btn_locator.first.click()
                page.wait_for_timeout(5000)
            if next_btn_locator.first.is_visible(timeout=5000):
                next_btn_locator.first.click()
                page.wait_for_timeout(5000)

            # Steps 7-9: Calendar Screenshots
            def advance_and_shoot(day_idx, filename):
                if day_idx > 0:
                    next_arrow = page.locator("button[aria-label*='next' i], button:has-text('>')").first
                    if next_arrow.is_visible(timeout=3000):
                        next_arrow.click()
                    page.wait_for_timeout(3500)
                page.screenshot(path=filename, full_page=True)
                return filename

            captured_screenshots.append((dates_list[0], advance_and_shoot(0, "day1_schedule.png")))
            captured_screenshots.append((dates_list[1], advance_and_shoot(1, "day2_schedule.png")))
            captured_screenshots.append((dates_list[2], advance_and_shoot(2, "day3_schedule.png")))

        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
            try:
                page.screenshot(path="fallback.png", full_page=True)
                captured_screenshots.append(("Fallback Page State", "fallback.png"))
            except:
                pass

        browser.close()

    # Email
    email_body = f"GFiber Webpass Schedule Report\nAddress: {TARGET_ADDRESS} #224\n\nTarget URL: {TARGET_URL}\nCheck attached debug and schedule screenshots."
    send_email_with_multiple_attachments("GFiber Webpass Run", email_body, captured_screenshots)

def send_email_with_multiple_attachments(subject, body, screenshots):
    sender_email = os.environ.get("SENDER_EMAIL", DEFAULT_SENDER).strip()
    sender_password = os.environ.get("SENDER_PASSWORD", "").replace(" ", "").strip()
    recipient_email_str = os.environ.get("RECIPIENT_EMAIL", DEFAULT_RECIPIENTS)
    recipients = [r.strip() for r in recipient_email_str.split(",") if r.strip()]

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(body, "plain"))

    for date_label, shot_path in screenshots:
        if os.path.exists(shot_path):
            try:
                with open(shot_path, "rb") as f:
                    img = MIMEImage(f.read(), name=os.path.basename(shot_path))
                    img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(shot_path))
                    msg.attach(img)
            except:
                pass

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipients, msg.as_string())
        server.quit()
    except Exception:
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipients, msg.as_string())
        except Exception as err:
            raise err

if __name__ == "__main__":
    run_agent()
