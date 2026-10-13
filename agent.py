import os
import smtplib
import traceback
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from playwright.sync_api import sync_playwright

TARGET_URL = "https://gfiber.com/webpass/signup/"
TARGET_ADDRESS = "18 10th Street San Francisco CA 94103"

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

        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print(f"Navigating to {TARGET_URL}...")
        try:
            page.goto(TARGET_URL, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(5000)

            # Step 1: Type Address
            print(f"Step 1: Targeting visible address input and typing {TARGET_ADDRESS}...")
            address_input = page.get_by_placeholder("Enter your address").locator("visible=true").first
            address_input.click(force=True)
            page.wait_for_timeout(1000)
            
            address_input.press_sequentially("18 10th Street San Francisco CA 9410", delay=150)
            page.wait_for_timeout(2000)
            address_input.press_sequentially("3", delay=200)
            page.wait_for_timeout(4000)

            # Step 2: Select Google Places Item
            print("Step 2: Clicking the Google Places dropdown...")
            pac_item = page.locator(".pac-container .pac-item").first
            if pac_item.is_visible(timeout=5000):
                pac_item.click(force=True)
                print("Clicked autocomplete suggestion!")
            else:
                address_input.press("ArrowDown")
                page.wait_for_timeout(1000)
                address_input.press("Enter")
            
            page.wait_for_timeout(4000)

            # Step 3: Select Unit
            print("Step 3: Clicking Unit field and selecting 224...")
            unit_field = page.locator("input[placeholder*='Unit' i], select[name*='unit' i], input[name*='unit' i]").locator("visible=true").first
            if unit_field.is_visible(timeout=5000):
                unit_field.click(force=True)
                page.wait_for_timeout(1000)
                
                if unit_field.evaluate("el => el.tagName.toLowerCase() === 'select'"):
                    try:
                        unit_field.select_option(label="224")
                    except:
                        unit_field.select_option(value="224")
                else:
                    unit_field.press_sequentially("224", delay=200)
                    page.wait_for_timeout(1500)
                    page.keyboard.press("ArrowDown")
                    page.wait_for_timeout(500)
                    page.keyboard.press("Enter")

            page.wait_for_timeout(3000)

            # Step 4: Click Check Availability
            print("Step 4: Clicking 'Check availability'...")
            check_button = page.locator("button:has-text('Check availability'), button:has-text('Check Availability')").locator("visible=true").first
            if check_button.is_visible(timeout=5000):
                check_button.click(force=True)
            else:
                page.keyboard.press("Enter")
            
            page.wait_for_timeout(8000)

            # Step 5: Click through intermediary screens
            print("Step 5: Clicking through intermediary 'Next' screens...")
            for i in range(3):
                next_btn = page.locator("button:has-text('Next'), button:has-text('Continue')").locator("visible=true").first
                if next_btn.is_visible(timeout=5000):
                    print(f"Clicking Next button (Screen {i+1})...")
                    next_btn.click(force=True)
                    page.wait_for_timeout(6000)
                
                # Verify if calendar has appeared
                calendar_check = page.locator("text='Select a date and time', [role='tab']")
                if calendar_check.count() > 0 and calendar_check.first.is_visible():
                    print("Successfully reached the appointment calendar!")
                    break

            page.wait_for_timeout(3000)

            # Step 6: Capture Calendar Screenshots
            print("Step 6: Capturing Calendar Screenshots...")
            def advance_and_shoot(day_idx, target_date_obj, filename):
                day_num_str = target_date_obj.strftime('%d').lstrip('0')
                print(f"Advancing to {target_date_obj.strftime('%A')} (Looking for date '{day_num_str}')...")
                
                # Force click the specific date every time, even for Day 1
                day_text_locator = page.get_by_text(day_num_str, exact=True).locator("visible=true").first
                tabs = page.locator("[role='tab']").locator("visible=true")
                
                if day_text_locator.is_visible(timeout=3000):
                    day_text_locator.click(force=True)
                    print(f"Clicked exact date '{day_num_str}' card.")
                elif tabs.count() > day_idx:
                    tabs.nth(day_idx).click(force=True)
                    print(f"Clicked structural tab index {day_idx}.")
                else:
                    print("Date card not found. Attempting to pan carousel...")
                    next_arrow = page.locator("button[aria-label*='next' i], button:has-text('>')").locator("visible=true").first
                    if next_arrow.is_visible(timeout=2000):
                        next_arrow.click(force=True)
                        page.wait_for_timeout(1500)
                        if day_text_locator.is_visible(timeout=2000):
                            day_text_locator.click(force=True)
                
                page.wait_for_timeout(4000) # Wait for slots to load
                
                print(f"Capturing screenshot -> {filename}")
                page.screenshot(path=filename, full_page=True)
                return filename

            # Capture Today (d1), Tomorrow (d2), Day After (d3) unconditionally
            captured_screenshots.append((dates_list[0], advance_and_shoot(0, d1, "day1_schedule.png")))
            captured_screenshots.append((dates_list[1], advance_and_shoot(1, d2, "day2_schedule.png")))
            captured_screenshots.append((dates_list[2], advance_and_shoot(2, d3, "day3_schedule.png")))

        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
            try:
                page.screenshot(path="fallback.png", full_page=True)
                captured_screenshots.append(("Fallback Page State", "fallback.png"))
            except:
                pass

        browser.close()

    # Format and send Email
    email_body = f"GFiber Webpass 3-Day Appointment Schedule Report\nAddress: {TARGET_ADDRESS} #224\n\nTarget URL: {TARGET_URL}\n\nAttached are the 3 installation schedule screenshots."
    send_email_with_multiple_attachments("GFiber Webpass Schedule (3 Days): 18 10th St #224", email_body, captured_screenshots)

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
