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

# Screenshot filenames
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
            print("Step 1: Typing '18 10th' into address input...")
            address_input = page.locator("input[placeholder*='address' i], input[type='text'], input[name*='address' i]").first
            address_input.click()
            address_input.fill("")
            address_input.press_sequentially("18 10th", delay=150)
            page.wait_for_timeout(2500)

            # Step 2: Select the first address in the dropdown menu
            print("Step 2: Selecting first address from autocomplete dropdown...")
            dropdown_item = page.locator(".pac-container .pac-item, [role='option'], .address-suggestion").first
            if dropdown_item.is_visible(timeout=5000):
                dropdown_item.click()
            else:
                address_input.press("ArrowDown")
                page.wait_for_timeout(300)
                address_input.press("Enter")
            page.wait_for_timeout(2500)

            # Step 3: Type 224 in the unit # field
            print("Step 3: Typing '224' into unit field...")
            unit_input = page.locator("input[placeholder*='Unit' i], input[placeholder*='Apt' i], input[name*='unit' i], [id*='unit' i]").first
            unit_input.click()
            unit_input.fill("")
            unit_input.press_sequentially("224", delay=150)
            page.wait_for_timeout(2000)

            # Step 4: Select unit # 224 from dropdown menu
            print("Step 4: Selecting unit 224 from unit dropdown...")
            unit_item = page.locator("[role='option']:has-text('224'), .unit-option:has-text('224'), .dropdown-menu :has-text('224')").first
            if unit_item.is_visible(timeout=3000):
                unit_item.click()
            else:
                unit_input.press("ArrowDown")
                page.wait_for_timeout(300)
                unit_input.press("Enter")
            page.wait_for_timeout(2500)

            # Step 5: Click 'Check availability' button
            print("Step 5: Clicking 'Check availability' button...")
            check_button = page.locator("button:has-text('Check availability'), button:has-text('Check Availability'), input[value*='Check' i]").first
            check_button.click()
            page.wait_for_timeout(5000)

            # Step 6: Click the "next" button on the new page
            print("Step 6: Clicking first 'Next' button...")
            next1_button = page.locator("button:has-text('Next'), a:has-text('Next'), input[value*='Next' i]").first
            if next1_button.is_visible(timeout=5000):
                next1_button.click()
                page.wait_for_timeout(5000)

            # Step 7: Click the "next" button on the second new page
            print("Step 7: Clicking second 'Next' button...")
            next2_button = page.locator("button:has-text('Next'), a:has-text('Next'), input[value*='Next' i]").first
            if next2_button.is_visible(timeout=5000):
                next2_button.click()
                page.wait_for_timeout(5000)

            # Step 8: Save Screenshot 1 (Day 1)
            print(f"Step 8: Saving Day 1 screenshot -> {SHOT_DAY1}")
            page.screenshot(path=SHOT_DAY1, full_page=True)
            captured_screenshots.append((dates_list[0], SHOT_DAY1))

            # Helper for clicking next day in calendar
            def click_next_day_button():
                next_day = page.locator(
                    "button[aria-label*='next day' i], "
                    "button[aria-label*='next' i], "
                    "[class*='next-day'], "
                    "[class*='calendar-next'], "
                    "[class*='arrow-right'], "
                    "button:has-text('>') "
                ).first
                if next_day.is_visible(timeout=3000):
                    next_day.click()
                else:
                    tabs = page.locator("[role='tab'], [class*='day-tab'], [class*='date-item']")
                    if tabs.count() > 1:
                        tabs.nth(1).click()
                page.wait_for_timeout(3500)

            # Step 9: Click Next Day button & Save Screenshot 2 (Day 2)
            print(f"Step 9: Clicking Next Day button and saving Day 2 screenshot -> {SHOT_DAY2}")
            click_next_day_button()
            page.screenshot(path=SHOT_DAY2, full_page=True)
            captured_screenshots.append((dates_list[1], SHOT_DAY2))

            # Step 10: Click Next Day button again & Save Screenshot 3 (Day 3)
            print(f"Step 10: Clicking Next Day button again and saving Day 3 screenshot -> {SHOT_DAY3}")
            click_next_day_button()
            page.screenshot(path=SHOT_DAY3, full_page=True)
            captured_screenshots.append((dates_list[2], SHOT_DAY3))

        except Exception as e:
            print(f"Warning during workflow execution: {e}")
            traceback.print_exc()

        browser.close()

    # Step 11: Send all 3 screenshots via email
    email_body = (
        "GFiber Webpass 3-Day Appointment Schedule Report\n"
        "Address: 18 10th Street, Unit 224, San Francisco, CA\n\n"
        "Attached are the 3 screenshots captured for each date view:\n"
        f"1. Day 1: {dates_list[0]}\n"
        f"2. Day 2: {dates_list[1]}\n"
        f"3. Day 3: {dates_list[2]}\n\n"
        f"Target URL: {TARGET_URL}"
    )

    send_email_with_multiple_attachments(
        subject=f"GFiber Webpass Schedule Screenshots (3 Days): 18 10th St #224",
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

    # Attach all available screenshots
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
