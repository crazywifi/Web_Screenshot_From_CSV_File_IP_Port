import os
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException

# Configuration
OUTPUT_FOLDER = "screenshots"
INPUT_FILE = input("Enter the CSV or Excel file name: ")

# Ensure output folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Set up Chrome in headless mode with extra settings
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-software-rasterizer")  # Prevents WebGL issues
chrome_options.add_argument("--disable-webgl")  # Disables WebGL
chrome_options.add_argument("--log-level=3")  # Suppress unnecessary logs

# Initialize WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def take_screenshot(url, filename, retries=2):
    """ Takes a screenshot of the given URL with error handling. """
    for attempt in range(retries):
        try:
            print(f"Trying: {url} (Attempt {attempt + 1})")
            driver.set_page_load_timeout(10)  # Limit load time
            driver.get(url)
            time.sleep(2)  # Allow page to fully load
            
            final_url = driver.current_url  # Get final resolved URL
            original_parsed = urlparse(url)
            final_parsed = urlparse(final_url)

            # Check for redirects
            if final_parsed.netloc != original_parsed.netloc or final_parsed.scheme != original_parsed.scheme:
                filename = filename.replace(".png", "_redirected.png")
                print(f"[REDIRECTED] {url} -> {final_url}")

            # Detect HTTP vs HTTPS
            if final_parsed.scheme == "https":
                print(f"[ENCRYPTED] {final_url}")
            else:
                print(f"[UNENCRYPTED] {final_url}")

            # Take screenshot
            driver.save_screenshot(filename)
            print(f"Screenshot saved: {filename}")
            return  # Exit function if successful
        
        except TimeoutException:
            print(f"⚠️ Timeout while accessing {url}. Retrying... ({attempt + 1}/{retries})")
        
        except WebDriverException as e:
            print(f"❌ WebDriver error for {url}: {e}")
            return  # Exit if it's a severe error

    print(f"❌ Failed to capture {url} after {retries} attempts.")

def main():
    """ Reads the input file and takes screenshots for each IP and Port combination. """
    try:
        # Read file (CSV or Excel)
        if INPUT_FILE.endswith(".csv"):
            df = pd.read_csv(INPUT_FILE)
        else:
            df = pd.read_excel(INPUT_FILE)

        # Ensure required columns exist
        if not {'IP', 'Port'}.issubset(df.columns):
            print("Error: Input file must have 'IP' and 'Port' columns")
            return
        
        for _, row in df.iterrows():
            ip, port = str(row['IP']), str(row['Port'])
            
            # Determine URL based on port
            urls = []
            if port == "80":
                urls.append((f"http://{ip}:{port}", "http"))
            elif port == "443":
                urls.append((f"https://{ip}:{port}", "https"))
            else:
                urls.append((f"http://{ip}:{port}", "http"))
                urls.append((f"https://{ip}:{port}", "https"))
            
            for url, protocol in urls:
                filename = os.path.join(OUTPUT_FOLDER, f"{protocol}_{ip}_{port}.png")
                take_screenshot(url, filename)

    except Exception as e:
        print(f"❌ Critical error: {e}")

    finally:
        # Close the browser when done
        driver.quit()
        print("✅ Finished capturing screenshots.")

if __name__ == "__main__":
    main()
