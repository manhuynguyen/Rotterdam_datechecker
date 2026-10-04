import datetime
import os
import urllib.parse
from bs4 import BeautifulSoup
import requests
from selenium import webdriver

# ==============================================================================
# CONFIGURATION
# ==============================================================================
# Read credentials from environment variables (GitHub Secrets) or fallback defaults
BOT_TOKEN = os.getenv('BOT_TOKEN', '8808264378:AAE07qApkQ-q7iYB4TwXjIkz-HGrPKW7hik')

# IMPORTANT: Update '5249' with your full numeric Telegram Chat ID (e.g., '123456789')
CHAT_ID = os.getenv('CHAT_ID', '5947953249')

TARGET_URL = 'https://concern.ir.rotterdam.nl/afspraak/maken/product/indienen-naturalisatieverzoek'


def send_telegram_message(message: str) -> None:
    """Send an HTTP GET request to Telegram API to notify the specified Chat ID."""
    encoded_message = urllib.parse.quote(message)
    send_text = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={encoded_message}'

    try:
        response = requests.get(send_text, timeout=10)
        if response.status_code == 200:
            print(f'Telegram message sent successfully to chat ID: {CHAT_ID}!')
        else:
            print(
                f'Failed to send message to chat ID: {CHAT_ID}. Status'
                f' code: {response.status_code}, response: {response.text}'
            )
    except Exception as e:
        print(f'Error sending Telegram request: {e}')


def setup_driver() -> webdriver.Chrome:
    """Configure Chrome for standard Linux CI environments like GitHub Actions."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        ' (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )

    return webdriver.Chrome(options=options)


def main():
    driver = setup_driver()
    try:
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(
            f'[{current_time}] Navigating to Rotterdam Naturalisation'
            ' page...'
        )

        driver.get(TARGET_URL)

        # Give dynamic JavaScript elements 8 seconds to load
        driver.implicitly_wait(8)

        # Parse page source with BeautifulSoup
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

    except Exception as e:
        print(f'An error occurred during execution: {e}')

    finally:
        driver.quit()
        print('Browser session closed.')


if __name__ == '__main__':
    main()
