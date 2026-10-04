import datetime
import time
import urllib.parse
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ==============================================================================
# CONFIGURATION
# ==============================================================================
BOT_TOKEN = '8808264378:AAE07qApkQ-q7iYB4TwXjIkz-HGrPKW7hik'  # Your Telegram Bot Token

# IMPORTANT: Replace '5249' with your full numeric Telegram Chat ID (e.g. '123456789')
CHAT_IDS = ['5947953249']

TARGET_URL = 'https://concern.ir.rotterdam.nl/afspraak/maken/product/indienen-naturalisatieverzoek'

# Check interval in seconds (300 seconds = 5 minutes)
CHECK_INTERVAL_SECONDS = 300


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================
def send_telegram_message(message: str) -> None:
    """Send an HTTP GET request to Telegram API to notify specified Chat IDs."""
    encoded_message = urllib.parse.quote(message)

    for chat_id in CHAT_IDS:
        send_text = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={chat_id}&text={encoded_message}'
        try:
            response = requests.get(send_text, timeout=10)
            if response.status_code == 200:
                print(
                    f'Telegram message sent successfully to chat ID: {chat_id}!'
                )
            else:
                print(
                    f'Failed to send message to chat ID: {chat_id}. Status'
                    f' code: {response.status_code}, response: {response.text}'
                )
        except Exception as e:
            print(f'Error sending Telegram request: {e}')


def setup_driver() -> webdriver.Chrome:
    """Configure headless Chrome options for cloud execution on Render."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')

    # Suppress background telemetry
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-component-update')

    return webdriver.Chrome(options=options)


def main():
    """Execute a single check on the Rotterdam appointment portal."""
    driver = setup_driver()
    try:
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(
            f'[{current_time}] Navigating to Rotterdam Naturalisation'
            ' page...'
        )

        driver.get(TARGET_URL)

        # Wait for the "Verder" button to become clickable and click it
        verder_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.NAME, 'verder'))
        )
        verder_button.click()

        # Brief wait for appointment slots to update in DOM
        time.sleep(5)

        # Parse page HTML with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        available_dates = soup.find_all(
            'button', class_='list-group-item-action'
        )
        alert_no_dates = soup.find_all('div', class_='alert-warning')

        if alert_no_dates:
            print('Alert box present: No available dates currently listed.')
            message_first_part = 'No available dates alert found.'
        else:
            message_first_part = 'Found active content on page.'

        active_dates = []
        for date_button in available_dates:
            # Only process buttons that are NOT disabled
            if date_button.get('disabled') is None:
                h3_tag = date_button.find('h3')
                p_tag = date_button.find('p')

                location = (
                    h3_tag.get_text(strip=True) if h3_tag else 'Rotterdam Office'
                )
                date_time = (
                    p_tag.get_text(strip=True)
                    if p_tag
                    else 'Date/Time unspecified'
                )

                active_dates.append(f'{location}: {date_time}')

        if active_dates:
            date_info = '\n'.join(active_dates)
            message = (
                f'🎉 APPOINTMENT DATES FOUND!\n\n'
                f'{message_first_part}\n\n'
                f'Available Slots:\n{date_info}\n\n'
                f'Checked at: {current_time}'
            )
            print(message)
            send_telegram_message(message)
        else:
            print('No active/enabled appointment buttons detected.')
            # Uncomment the next line if you want notifications even when NO dates are available:
            # send_telegram_message(f"{message_first_part}\nNo available dates found.\nChecked at: {current_time}")

    except Exception as e:
        print(f'An error occurred during execution: {e}')

    finally:
        driver.quit()
        print('Browser driver closed safely.')


# ==============================================================================
# CONTINUOUS EXECUTION LOOP
# ==============================================================================
if __name__ == '__main__':
    print('====================================================')
    print('Starting Rotterdam Naturalisation Appointment Monitor')
    print(
        f'Checking every {CHECK_INTERVAL_SECONDS // 60} minutes. Press Ctrl+C'
        ' in terminal to stop.'
    )
    print('====================================================\n')

    while True:
        try:
            main()
        except KeyboardInterrupt:
            print('\nScript manually stopped by user.')
            break
        except Exception as e:
            print(f'Unexpected loop error encountered: {e}')

        print(
            f'Sleeping for {CHECK_INTERVAL_SECONDS // 60} minutes until next'
            ' check...\n'
        )
        time.sleep(CHECK_INTERVAL_SECONDS)
