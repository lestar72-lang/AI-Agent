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
        print("Launching browser context...")
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print(f"Navigating to {TARGET_URL}...")
        try:
            page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)

            # Step 1: Type "18 10th"
            print("Step 1: Typing address into input field...")
            address_input = page.locator("input[placeholder*='address' i], input[type='text'], input[name*='address' i]").first
            address_input.click()
            address_input.fill("")
            address_input.type("18 10th", delay=150)
            page.wait_for_timeout(3000)

            # Step 2: Click Google Autocomplete item
            print("Step 2: Selecting address from Google Places autocomplete dropdown...")
            pac_item = page.locator(".pac-container .pac-item, [role='option'], .address-suggestion").first
            try:
                pac_item.wait_for(state="visible", timeout=5000)
                pac_item.click()
            except Exception:
                print("Fallback: Pressing ArrowDown + Enter for autocomplete")
                address_input.press("ArrowDown")
                page.wait_for_timeout(500)
                address_input.press("Enter")
            page.wait_for_timeout(3000)

            # Step 3: Click Unit # and type "224"
            print("Step 3: Selecting Unit # 224...")
            unit_field = page.locator("input[placeholder*='Unit' i], input[name*='unit' i], select[name*='unit' i], [id*='unit' i]").first
            unit_field.click()
            page.wait_for_timeout(500)

            if unit_field.evaluate("el => el.tagName.toLowerCase() === 'select'"):
                try:
                    unit_field.select_option(label="224")
                except Exception:
                    unit_field.select_option(value="224")
            else:
                unit_field.fill("")
                unit_field.type("224", delay=100)
                page.wait_for_timeout(1000)
                
                # Check for unit dropdown options
                unit_option = page.locator("[role='option']:has-text('224'), .dropdown-item:has-text('224'), text='224'").first
                if unit_option.is_visible(timeout=2000):
                    unit_option.click()
                else:
                    unit_field.press("Enter")

            page.wait_for_timeout(2000)

            # Step 4: Click Check Availability
            print("Step 4: Clicking 'Check availability' button...")
            check_button = page.locator("button:has-text('Check availability'), button:has-text('Check Availability'), input[value*='Check' i]").first
            check_button.click()
            page.wait_for_timeout(6000)

            # Step 5: Click First "Next" Button
            print("Step 5: Clicking first 'Next' button...")
            next1_button = page.locator("button:has-text('Next'), a:has-text('Next'), input[value*='Next' i], button.next-btn").first
            if next1_button.is_visible(timeout=5000):
                next1_button.click()
                page.wait_for_timeout(5000)

            # Step 6: Click Second "Next" Button
            print("Step 6: Clicking second 'Next' button...")
            next2_button = page.locator("button:has-text('Next'), a:has-text('Next'), input[value*='Next' i], button.next-btn").first
            if next2_button.is_visible(timeout=5000):
                next2_button.click()
                page.wait_for_timeout(5000)

            print("Waiting for Installation Calendar screen...")
            page.wait_for_timeout(4000)

            # Step 7: Screenshot Day 1 (Calendar view)
            print(f"Step 7: Saving Day 1 screenshot -> {SHOT_DAY1}")
            page.screenshot(path=SHOT_DAY1, full_page=True)
            captured_screenshots.append((dates_list[0], SHOT_DAY1))

            # Helper function to switch calendar date tabs
            def advance_calendar_day(day_index):
                # First try clicking the date card directly (e.g. Day 2 or Day 3 card)
                date_cards = page.locator("[class*='date'], [class*='day'], [role='tab']")
                next_arrow = page.locator("button[aria-label*='next' i], [class*='arrow-right'], button:has-text('>')").first

                if date_cards.count() > day_index:
                    print(f"Clicking date card index {day_index}...")
                    date_cards.nth(day_index).click()
                elif next_arrow.is_visible(timeout=2000):
                    print("Clicking next arrow on calendar...")
                    next_arrow.click()
                
                page.wait_for_timeout(3500)

            # Step 8: Advance to Day 2 and Screenshot
            print(f"Step 8: Advancing to Day 2 and saving screenshot -> {SHOT_DAY2}")
            advance_calendar_day(1)
            page.screenshot(path=SHOT_DAY2, full_page=True)
            captured_screenshots.append((dates_list[1], SHOT_DAY2))

            # Step 9: Advance to Day 3 and Screenshot
            print(f"Step 9: Advancing to Day 3 and saving screenshot -> {SHOT_DAY3}")
            advance_calendar_day(2)
            page.screenshot(path=SHOT_DAY3, full_page=True)
            captured_screenshots.append((dates_list[2], SHOT_DAY3))

        except Exception as e:
            print(f"Warning during workflow execution: {e}")
            traceback.print_exc()

        browser.close()

    # Step 10: Email the 3 screenshots
    email_body = (
        "GFiber Webpass 3-Day Appointment Schedule Report\n"
        "Address: 18 10th Street, Unit 224, San Francisco, CA\n\n"
        "Attached are the 3 installation schedule screenshots:\n"
        f"1. {dates_list[0]}\n"
        f"2. {dates_list[1]}\n"
        f"3. {dates_list[2]}\n\n"
        f"Target URL: {TARGET_URL}"
    )

    send_email_with_multiple_attachments(
        subject="GFiber Webpass Installation Schedule (3 Days): 18 10th St #224",
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
        print("SUCCESS: Email sent with all 3 screenshots via Port 587!")
    except Exception as err_587:
        print(f"Port 587 failed ({err_587}), trying Port 465...")
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipients, msg.as_string())
            print("SUCCESS: Email sent with all 3 screenshots via Port 465!")
        except Exception as err_465:
            traceback.print_exc()
            raise err_465

if __name__ == "__main__":
    run_agent()
