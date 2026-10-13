import os
import smtplib
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright

TARGET_URL = "https://gfiber.com/webpass/signup/?utm_campaign=searchomfsanfrancisco&utm_content=one-month-free&utm_medium=ga-search&utm_source=dynamic-ads&utm_term=marketing&gad_source=1"

DEFAULT_SENDER = "lestera@gfiber.com"
DEFAULT_RECIPIENTS = "rgalvin@gfiber.com, lestar72@gmail.com"

def run_agent():
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Navigating to {TARGET_URL}...")
        try:
            # Use domcontentloaded instead of networkidle to prevent analytics timeout
            page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)  # Wait 5 seconds for dynamic JS components
        except Exception as e:
            print(f"Warning during page load: {e}")

        # Query appointment time slots or related elements
        time_elements = page.query_selector_all('[class*="slot"], [class*="appointment"], [class*="time"]')
        
        extracted_times = []
        if time_elements:
            for elem in time_elements:
                text = elem.inner_text().strip()
                if text and text not in extracted_times:
                    extracted_times.append(text)

        # Fallback text parser if specific CSS classes aren't matched
        if not extracted_times:
            body_text = page.inner_text("body")
            extracted_times = [
                line.strip() 
                for line in body_text.split("\n") 
                if any(char.isdigit() for char in line) and ("AM" in line or "PM" in line)
            ]

        browser.close()

    # Format output email
    if extracted_times:
        results_summary = "\n".join([f"- {t}" for t in extracted_times])
    else:
        results_summary = "No explicitly formatted appointment times were detected on the page today."

    email_body = f"Here are today's available GFiber Webpass appointment times:\n\n{results_summary}\n\nChecked page: {TARGET_URL}"

    send_email(
        subject="GFiber Webpass: Daily Available Appointment Times", 
        body=email_body
    )

def send_email(subject, body):
    # Fetch environment variables or fall back to defaults
    sender_email = os.environ.get("SENDER_EMAIL", DEFAULT_SENDER)
    sender_password = os.environ.get("SENDER_PASSWORD", "ywijnwldffuheasn")
    recipient_email_str = os.environ.get("RECIPIENT_EMAIL", DEFAULT_RECIPIENTS)

    # Clean app password formatting
    sender_password = sender_password.replace(" ", "")

    recipients = [r.strip() for r in recipient_email_str.split(",") if r.strip()]

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipients)

    try:
        print(f"Connecting to SMTP server and sending email to: {', '.join(recipients)}...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipients, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
        # Raise error so GitHub workflow marks execution failure on bad credentials
        raise e

if __name__ == "__main__":
    run_agent()
