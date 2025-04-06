import json
from playwright.sync_api import sync_playwright
import time
import os
import datetime
from tqdm import tqdm

# Path to Chrome executable
chrome_executable_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
# Path to your extension (update this with your extension path)
extension_path = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'post_exporter')
netscape_cookie_file = "cookies.txt"


def get_cookies(context, txt_file):
    """Convert Netscape cookies.txt format to JSON format for Playwright."""
    cookies = []
    with open(txt_file, "r") as f:
        for line in f:
            if line.startswith("#") or line.strip() == "":
                continue
            parts = line.strip().split("\t")
            if len(parts) < 7:
                continue
            cookie = {
                "domain": parts[0],
                "httpOnly": parts[1].lower() == "true",
                "path": parts[2],
                "secure": parts[3].lower() == "true",
                "expires": int(parts[4]) if parts[4].isdigit() else None,
                "name": parts[5],
                "value": parts[6],
            }
            cookies.append(cookie)
    context.add_cookies(cookies)


def main():
    with sync_playwright() as p:
        args = [
            f'--disable-extensions-except={extension_path}',
            f'--load-extension={extension_path}',
            '--start-maximized',
        ]

        context = p.chromium.launch_persistent_context(
            user_data_dir="playwright_user_data",  # Persistent session
            executable_path=chrome_executable_path,
            headless=False,
            args=args
        )
        context.grant_permissions(
            ["clipboard-read", "clipboard-write"], origin="https://www.facebook.com")
        get_cookies(context, netscape_cookie_file)

        # Get the extension ID (for manifest v3)
        service_workers = context.service_workers
        extension_id = None

        # Wait for service worker to be available (manifest v3)
        if not service_workers:
            print("Waiting for extension service worker...")
            service_worker = context.wait_for_event('serviceworker')
            # extension_id = service_worker.url.split('/')[2]
        else:
            # extension_id = service_workers[0].url.split('/')[2]
            pass

        fb_group_urls = [
            "https://www.facebook.com/groups/tuidepcaudep/?sorting_setting=CHRONOLOGICAL",
            "https://www.facebook.com/groups/1085204171983972/?sorting_setting=CHRONOLOGICAL"
        ]

        # Use tqdm to display a progress bar for URLs
        for url in tqdm(fb_group_urls, desc="Processing Facebook Groups"):
            # Create a new page and navigate to Facebook group
            page = context.new_page()
            page.goto(url)

            get_posts(page, 5)
            # Close the page when done
            page.close()
        # Close the browser context when done
        context.close()


def get_posts(page, number_of_posts=10):
    # Try to find and click the "Download These Posts" button
    try:
        # Using CSS selector to find the button with specific characteristics
        # Look for a button with the extension logo inside
        button_selector = 'button.ant-btn.css-z5ern8:has(span.ant-avatar)'
        
        # Wait for the button to appear with timeout
        page.wait_for_selector(button_selector, timeout=3000)  # 3 seconds timeout
        
        button = page.locator(button_selector)
        if button.count() == 0:
            # reload the page if button still not found after waiting
            page.reload()
            # Wait again after reload
            page.wait_for_selector(button_selector, timeout=30000)
            button = page.locator(button_selector)
            
        # Click the button
        button.click()

        # Wait for any potential response or action after clicking
        # page.wait_for_timeout(5000)  # Wait 5 seconds

        # Explicitly ensure Gen-HTML is checked (even if it appears checked by default)
        # Wait for the checkbox to exist before attempting to interact with it
        page.wait_for_selector('input.ant-checkbox-input[type="checkbox"]', timeout=10000)
        gen_html_checkbox = page.locator(
            'input.ant-checkbox-input[type="checkbox"]').nth(1)
        if not gen_html_checkbox.is_checked():
            gen_html_checkbox.check()

        # Set Request Delay to 1 second
        delay_input = page.locator('.ant-input-number-input')
        delay_input.fill('1.0')  # Set to 1 second

        # Ensure "By posts count" is selected
        posts_count_radio = page.locator('.ant-radio-input[value="1"]')
        if not posts_count_radio.is_checked():
            posts_count_radio.check()

        # Wait to ensure the UI is fully loaded
        # page.wait_for_timeout(1000)

        # Finally click the Start button
        start_button = page.locator('button.ant-btn-primary:has-text("Start")')
        start_button.click()

        try:
            # Wait for either:
            # 1. Success message to appear
            # 2. Start button to become enabled again (meaning the process is done)
            # 3. Download buttons to appear
            completion_selector = [
                ".ant-result-success",  # Success message
                # Start button re-enabled
                "button.ant-btn-primary:not([disabled]):has-text('Start')",
                "button:has-text('Clipboard')"  # Download buttons appear
            ]

            # Wait for any of these conditions with timeout
            page.wait_for_selector(
                f"{', '.join(completion_selector)}", timeout=120000)

        except Exception as e:
            print(f"Timeout waiting for completion: {e}")


        # Look for and click the Clipboard button (changed from "Clipboard")
        page.wait_for_selector('button:has-text("Clipboard")', timeout=10000)
        clipboard_button = page.locator('button:has-text("Clipboard")')
        if clipboard_button.count() > 0:
            clipboard_button.click()
            # Wait a moment for the clipboard operation to complete
            page.wait_for_timeout(2000)

            # Now try to read the clipboard
            clipboard_content = page.evaluate("""
                (async function() {
                    try {
                        return await navigator.clipboard.readText();
                    } catch (err) {
                        console.error('Failed to read clipboard:', err);
                        return null;
                    }
                })()
            """)

            if clipboard_content:
                # Create a filename with timestamp
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"facebook_posts_{timestamp}.csv"

                # Save the content to a CSV file
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(clipboard_content)

            else:
                print("Failed to get content from clipboard")
        else:
            print("CSV button not found")
    except Exception as e:
        pass


if __name__ == "__main__":
    main()
