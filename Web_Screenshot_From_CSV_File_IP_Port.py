import os
import pandas as pd
import asyncio
from pyppeteer import launch
from urllib.parse import urlparse

# Configuration
OUTPUT_FOLDER = "screenshots"
BROWSER_PATH = os.path.join(os.getcwd(), "chrome-win", "chrome-win", "chrome.exe")

# Ask user for input file
INPUT_FILE = input("Enter the CSV or Excel file name: ")

async def take_screenshot(browser, url, filename):
    try:
        page = await browser.newPage()
        response = await page.goto(url, {'waitUntil': 'networkidle2', 'timeout': 30000})
        final_url = page.url  # Get the final resolved URL
        
        # Check if the URL was actually redirected (hostname, protocol, or path changed)
        original_parsed = urlparse(url)
        final_parsed = urlparse(final_url)
        
        if (final_parsed.netloc != original_parsed.netloc or
            final_parsed.scheme != original_parsed.scheme or
            final_parsed.path != original_parsed.path):
            filename = filename.replace(".png", "_redirected.png")
            print(f"[REDIRECTED] {url} -> {final_url}")
        
        # Determine if the communication is encrypted or unencrypted
        if final_parsed.scheme == "https":
            print(f"[ENCRYPTED] {final_url}")
        else:
            print(f"[UNENCRYPTED] {final_url}")
        
        await page.screenshot({'path': filename, 'fullPage': True})
        await page.close()
        print(f"Screenshot saved: {filename}")
    except Exception as e:
        print(f"Failed to capture {url}: {e}")

async def main():
    # Create output folder if not exists
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # Read file (CSV or Excel)
    if INPUT_FILE.endswith(".csv"):
        df = pd.read_csv(INPUT_FILE)
    else:
        df = pd.read_excel(INPUT_FILE)
    
    # Ensure required columns exist
    if not {'IP', 'Port'}.issubset(df.columns):
        print("Error: Input file must have 'IP' and 'Port' columns")
        return
    
    try:
        browser = await launch(headless=True, executablePath=BROWSER_PATH)
        tasks = []
        for index, row in df.iterrows():
            ip, port = str(row['IP']), str(row['Port'])
            
            # Ensure correct protocol based on port
            if port == "80":
                urls = [(f"http://{ip}:{port}", "http")]
            elif port == "443":
                urls = [(f"https://{ip}:{port}", "https")]
            else:
                urls = [(f"http://{ip}:{port}", "http"), (f"https://{ip}:{port}", "https")]
            
            for url, protocol in urls:
                filename = os.path.join(OUTPUT_FOLDER, f"{protocol}_{ip}_{port}.png")
                tasks.append(take_screenshot(browser, url, filename))
        
        # Run tasks concurrently
        await asyncio.gather(*tasks)
    except Exception as e:
        print(f"Browser launch failed: {e}")
    finally:
        if 'browser' in locals() and browser:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
