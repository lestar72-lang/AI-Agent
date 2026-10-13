import os
import smtplib
import traceback
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from playwright.sync_api import sync_playwright

TARGET_URL = "https://gfiber.com/webpass/signup/?utm_campaign=searchomfsanfrancisco&utm_content=one-month-free&utm_medium=ga-search&utm_source=dynamic-ads&utm_term=marketing&gad_source=1"

DEFAULT_SENDER = "lestar72@gmail.com"
DEFAULT_RECIPIENTS = "rgalvin@gfiber.com, lestar72@gmail.com"

SHOT_DAY1 = "day1_schedule.png"
SHOT_DAY2 = "day2_schedule.png"
SHOT_DAY3 = "day3_schedule.png"

def run_agent():
    print("=== STARTING AGENT RUN ===")
    
    d1 = datetime.now()
    d2 = d1 + timedelta(days=1)
    d3 = d1 + timedelta(days=2)
    
    dates_list = [
        d1.strftime("%A, %B %d, %Y"),
        d2.strftime("%A, %B %d, %Y"),
        d3.strftime("%A, %B %d, %Y")
    ]

    captured_screenshots = []

    with sync_playwright() as p:
        print("Launching Chromium browser context...")
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/Los_Angeles"
        )
        page = context.new_page()

        # Stealth script injections to trick Google Places API anti-bot detection
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """)

        print(f"Navigating to {TARGET_URL}...")
        try:
            page.goto(TARGET_URL, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)

            # Step 1: Click and type into address box
            print("Step 1: Typing '18 10th' into address box...")
            address_input = page.locator("input[placeholder*='address' i], input[type='text']").first
            address_input.click()
            address_input.fill("")
            page.wait_for_timeout(500)
            
            address_input.press_sequentially("18 10th", delay=180)
            page.wait_for_timeout(3000)

            # Step 2: Force Google Autocomplete suggestion selection via DOM dispatch
            print("Step 2: Triggering Google Places suggestion selection...")
            pac_item = page.locator(".pac-container .pac-item").first
            
            try:
                pac_item.wait_for(state="visible", timeout=7000)
                pac_item.hover()
                pac_item.click(force=True)
                print("Successfully clicked Google Places autocomplete item!")
            except Exception:
                print("Falling back to native ArrowDown + Enter key press...")
                page.keyboard.press("ArrowDown")
                page.wait_for_timeout(500)
                page.keyboard.press("Enter")

            page.wait_for_timeout(3500)

            # Step 3: Click Unit field and select 224
            print("Step 3: Selecting Unit 224...")
            unit_element = page.locator("input[placeholder*='Unit' i], select[name*='unit' i], input[name*='unit' i], [id*='unit' i]").first
            
            if unit_element.is_visible(timeout=5000):
                unit_element.click()
                page.wait_for_timeout(500)

                if unit_element.evaluate("el => el.tagName.toLowerCase() === 'select'"):
                    try:
                        unit_element.select_option(label="224")
                    except Exception:
                        unit_element.select_option(value="224")
                else:
                    unit_element.fill("224")
                    page.wait_for_timeout(500)
                    unit_option = page.locator("[role='option']:has-text('224'), .dropdown-item:has-text('224'), text='224'").first
                    if unit_option.is_visible(timeout=2000):
                        unit_option.click()
                    else:
                        page.keyboard.press("Enter")

            page.wait_for_timeout(2500)

            # Step 4: Click 'Check availability'
            print("Step 4: Clicking 'Check availability' button...")
            check_button = page.locator("button:has-text('Check availability'), button:has-text('Check Availability'), input[value*='Check' i]").first
            check_button.click()
            page.wait_for_timeout(6000)

            # Step 5: Click first Next button
            print("Step 5: Clicking first 'Next' button...")
            next1 = page.locator("button:has-text('Next'), a:has-text('Next'), input[value*='Next' i]").first
            if next1.is_visible(timeout=5000):
                next1.click()
                page.wait_for_timeout(5000)

            # Step 6: Click second Next button
            print("Step 6: Clicking second 'Next' button...")
            next2 = page.locator("button:has-text('Next'), a:has-text('Next'), input[value*='Next' i]").first
            if next2.is_visible(timeout=5000):
                next2.click()
                page.wait_for_timeout(5000)

            print("Waiting for calendar schedule page...")
            page.wait_for_timeout(4000)

            # Step 7: Screenshot Day 1
            print(f"Step 7: Capturing Day 1 Screenshot -> {SHOT_DAY1}")
            page.screenshot(path=SHOT_DAY1, full_page=True)
            captured_screenshots.append((dates_list[0], SHOT_DAY1))

            # Helper function to switch calendar date tabs
            def advance_calendar_day(day_idx):
                date_cards = page.locator("[role='tab'], [class*='card'], [class*='day'], [class*='date']")
                next_arrow = page.locator("button[aria-label*='next' i], [class*='arrow-right'], button:has-text('>')").first

                if date_cards.count() > day_idx:
                    date_cards.nth(day_idx).click()
                elif next_arrow.is_visible(timeout=2000):
                    next_arrow.click()
                
                page.wait_for_timeout(3500)

            # Step 8: Click Next Date GUI & Screenshot Day 2
            print(f"Step 8: Advancing to Day 2 and capturing screenshot -> {SHOT_DAY2}")
            advance_calendar_day(1)
            page.screenshot(path=SHOT_DAY2, full_page=True)
            captured_screenshots.append((dates_list[1], SHOT_DAY2))

            # Step 9: Click Next Date GUI & Screenshot Day 3
            print(f"Step 9: Advancing to Day 3 and capturing screenshot -> {SHOT_DAY3}")
            advance_calendar_day(2)
            page.screenshot(path=SHOT_DAY3, full_page=True)
            captured_screenshots.append((dates_list[2], SHOT_DAY3))

        except Exception as e:
            print(f"Error during execution: {e}")
            traceback.print_exc()

        browser.close()

    # Step 10: Email the 3 screenshots
    email_body = (
        "GFiber Webpass 3-Day Appointment Schedule Report\n"
        "Address: 18 10th Street, Unit 224, San Francisco, CA\n\n"
        "Attached are the installation schedule screenshots:\n"
        f"1. {dates_list[0]}\n"
        f"2. {dates_list[1]}\n"
        f"3. {dates_list[2]}\n\n"
        f"Target URL: {TARGET_URL}"
    )

    send_email_with_multiple_attachments(
        subject="GFiber Webpass Schedule Screenshots (3 Days): 18 10th St #224",
        body=email_body,
        screenshots=captured_screenshots
    )

def send_email_with_multiple_attachments(subject, body, screenshots):
    sender_email = os.environ.get("SENDER_EMAIL", DEFAULT_SENDER).strip()
    sender_password = os.environ.get("SENDER_PASSWORD", "").replace(" ", "").strip()
    recipient_email_str = os.environ.get("RECIPIENT_EMAIL", DEFAULT_RECIPIENTS)

    if not sender_password:
        print("ERROR: SENDER_PASSWORD secret is missing or empty in GitHub Secrets!")
        raise ValueError("Missing SENDER_PASSWORD environment variable.")

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
                    print(f"Attached screenshot for {date_label} ({shot_path})")
            except Exception as att_err:
                print(f"Failed attaching {shot_path}: {att_err}")

    print(f"Sending email to: {', '.join(recipients)}...")
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipients, msg.as_string())
        server.quit()
        print("SUCCESS: Email sent with screenshots via Port 587!")
    except Exception as err_587:
        print(f"Port 587 failed ({err_587}), trying Port 465...")
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipients, msg.as_string())
            print("SUCCESS: Email sent with screenshots via Port 465!")
        except Exception as err_465:
            traceback.print_exc()
            raise err_465

if __name__ == "__main__":
    run_agent()
    
