import os
import smtplib
import traceback
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from playwright.sync_api import sync_playwright

TARGET_URL = "https://gfiber.com/webpass/signup/?utm_campaign=searchomfsanfrancisco&utm_content=one-month-free&utm_medium=ga-search&utm_source=dynamic-ads&utm_term=marketing&gad_source=1"
TARGET_ADDRESS = "18 10th Street, San Francisco, CA, USA"
TARGET_UNIT = "224"

DEFAULT_SENDER = "lestar72@gmail.com"
DEFAULT_RECIPIENTS = "rgalvin@gfiber.com, lestar72@gmail.com"
SCREENSHOT_PATH = "appointments_schedule.png"

def run_agent():
    print("=== STARTING AGENT RUN ===")
    
    # Calculate target dates
    d1 = datetime.now()
    d2 = d1 + timedelta(days=1)
    d3 = d1 + timedelta(days=2)
    
    dates_list = [
        d1.strftime("%A, %B %d, %Y"),
        d2.strftime("%A, %B %d, %Y"),
        d3.strftime("%A, %B %d, %Y")
    ]

    daily_results = {}

    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        # Standard desktop viewport to ensure clean screenshot rendering
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        print(f"Navigating to {TARGET_URL}...")
        try:
            page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)

            # Step 1: Enter street address
            print(f"Entering address: {TARGET_ADDRESS}")
            address_input = page.locator("input[placeholder*='address' i], input[type='text']").first
            address_input.click()
            address_input.fill(TARGET_ADDRESS)
            page.wait_for_timeout(2000)

            # Select address from Google/autocomplete dropdown
            try:
                page.locator(".pac-container .pac-item, [role='option'], .address-suggestion").first.click(timeout=3000)
            except Exception:
                address_input.press("Enter")
            
            page.wait_for_timeout(3000)

            # Step 2: Select Unit 224
            print(f"Selecting Unit: {TARGET_UNIT}")
            unit_dropdown = page.locator("select[name*='unit' i], select[id*='unit' i], [role='combobox']").first
            
            if unit_dropdown.is_visible():
                try:
                    unit_dropdown.select_option(label=TARGET_UNIT)
                except Exception:
                    unit_dropdown.select_option(value=TARGET_UNIT)
            else:
                page.locator("[placeholder*='unit' i], [placeholder*='apt' i], text=Unit").click()
                page.locator(f"text='{TARGET_UNIT}'").click()

            page.wait_for_timeout(2000)

            # Step 3: Click 'Check Availability'
            print("Clicking 'Check Availability' button...")
            check_button = page.locator("button:has-text('Check availability'), button:has-text('Check Availability'), input[value*='Check availability' i]").first
            if check_button.is_visible():
                check_button.click()
            else:
                page.locator("button[type='submit'], button:has-text('Check'), button:has-text('Continue')").first.click()

            page.wait_for_timeout(5000)

            # Step 4: Click 'Next'
            print("Clicking 'Next' button...")
            next_button = page.locator("button:has-text('Next'), a:has-text('Next'), input[value*='Next' i]").first
            if next_button.is_visible():
                next_button.click()
                page.wait_for_timeout(5000)
            else:
                page.locator("button[type='submit'], button:has-text('Continue')").first.click()
                page.wait_for_timeout(5000)

            print("Waiting for initial appointment slots page to load...")
            page.wait_for_timeout(4000)

            # Function to scrape current day slots
            def extract_slots():
                time_elements = page.query_selector_all('[class*="slot"], [class*="appointment"], [class*="time"], [class*="schedule"]')
                extracted = []
                if time_elements:
                    for elem in time_elements:
                        text = elem.inner_text().strip()
                        if text and text not in extracted:
                            extracted.append(text)
                if not extracted:
                    body_text = page.inner_text("body")
                    extracted = [
                        line.strip() 
                        for line in body_text.split("\n") 
                        if any(char.isdigit() for char in line) and ("AM" in line or "PM" in line)
                    ]
                return extracted

            # Function to click next day arrow/tab
            def click_next_day(step_num):
                print(f"Clicking Next Day in calendar GUI (Step {step_num})...")
                next_day_selector = page.locator(
                    "button[aria-label*='next day' i], "
                    "button[aria-label*='next' i], "
                    "[class*='next-day'], "
                    "[class*='calendar-next'], "
                    "[class*='arrow-right'], "
                    "button:has-text('>') "
                ).first

                if next_day_selector.is_visible():
                    next_day_selector.click()
                    print(f"Clicked Next Day button successfully (Step {step_num}).")
                    page.wait_for_timeout(3000)
                else:
                    date_tabs = page.locator("[role='tab'], [class*='day-tab'], [class*='date-item']")
                    if date_tabs.count() > step_num:
                        date_tabs.nth(step_num).click()
                        page.wait_for_timeout(3000)

            # --- Day 1 (Today) ---
            print(f"Scraping Day 1 ({dates_list[0]})...")
            daily_results[dates_list[0]] = extract_slots()

            # --- Day 2 (Tomorrow) ---
            click_next_day(1)
            print(f"Scraping Day 2 ({dates_list[1]})...")
            daily_results[dates_list[1]] = extract_slots()

            # --- Day 3 (Day After Tomorrow) ---
            click_next_day(2)
            print(f"Scraping Day 3 ({dates_list[2]})...")
            daily_results[dates_list[2]] = extract_slots()

            # Step 5: Capture Screenshot
            print(f"Taking screenshot of appointment schedule -> {SCREENSHOT_PATH}...")
            page.screenshot(path=SCREENSHOT_PATH, full_page=True)

        except Exception as e:
            print(f"Warning during calendar navigation: {e}")
            # Ensure we try taking screenshot even if navigation had warnings
            try:
                page.screenshot(path=SCREENSHOT_PATH, full_page=True)
            except Exception:
                pass

        browser.close()

    # Format 3-Day Email Body
    email_body = f"GFiber Webpass 3-Day Availability Report\n"
    email_body += f"Address: {TARGET_ADDRESS}, Unit {TARGET_UNIT}\n"
    email_body += f"Generated on: {dates_list[0]}\n"
    email_body += "==================================================\n\n"

    for date_str, slots in daily_results.items():
        email_body += f"📅 {date_str.upper()}\n"
        if slots:
            email_body += "\n".join([f"   • {slot}" for slot in slots])
        else:
            email_body += "   (No open appointment slots detected for this date)"
        email_body += "\n\n"

    email_body += f"A full screenshot of the appointment schedule is attached to this email.\n\nTarget Page: {TARGET_URL}"

    subject_line = f"GFiber Webpass 3-Day Appointments: {TARGET_ADDRESS} #224"

    send_email_with_attachment(
        subject=subject_line,
        body=email_body,
        attachment_path=SCREENSHOT_PATH if os.path.exists(SCREENSHOT_PATH) else None
    )

def send_email_with_attachment(subject, body, attachment_path=None):
    sender_email = os.environ.get("SENDER_EMAIL", DEFAULT_SENDER).strip()
    sender_password = os.environ.get("SENDER_PASSWORD", "").replace(" ", "").strip()
    recipient_email_str = os.environ.get("RECIPIENT_EMAIL", DEFAULT_RECIPIENTS)

    if not sender_password:
        print("ERROR: SENDER_PASSWORD secret is missing or empty in GitHub Secrets!")
        raise ValueError("Missing SENDER_PASSWORD environment variable.")

    recipients = [r.strip() for r in recipient_email_str.split(",") if r.strip()]

    # Create Multipart MIME Message for text + image attachment
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipients)

    # Attach text body
    msg.attach(MIMEText(body, "plain"))

    # Attach PNG screenshot if present
    if attachment_path and os.path.exists(attachment_path):
        try:
            with open(attachment_path, "rb") as f:
                img_data = f.read()
                image_attachment = MIMEImage(img_data, name=os.path.basename(attachment_path))
                msg.attach(image_attachment)
                print("Successfully attached appointment schedule screenshot.")
        except Exception as img_err:
            print(f"Warning: Failed to attach screenshot image: {img_err}")

    print(f"Connecting to SMTP server to send email from {sender_email} to: {', '.join(recipients)}...")
    
    # Try Port 587 (STARTTLS) first, then fallback to Port 465 (SSL)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipients, msg.as_string())
        server.quit()
        print("SUCCESS: Email sent successfully via Port 587 (STARTTLS)!")
    except Exception as err_587:
        print(f"Port 587 failed ({err_587}), attempting Port 465 (SSL)...")
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipients, msg.as_string())
            print("SUCCESS: Email sent successfully via Port 465 (SSL)!")
        except Exception as err_465:
            print("!!! EMAIL SENDING ERROR DETAILED BELOW !!!")
            traceback.print_exc()
            raise err_465

if __name__ == "__main__":
    run_agent()
