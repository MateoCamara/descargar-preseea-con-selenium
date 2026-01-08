import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuration
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
BASE_URL = "https://preseea.uah.es/index.php/corpus-preseea"

# Create download directory if it doesn't exist
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def get_filename_from_cd(cd):
    """
    Get filename from content-disposition
    """
    if not cd:
        return None
    fname = None
    if 'filename=' in cd:
        fname = cd.split('filename=')[1]
        if '"' in fname:
            fname = fname.split('"')[1]
    return fname

def download_file(url, session_cookies):
    """
    Download file using requests with cookies from selenium session
    to avoid dealing with browser download popups/renaming.
    """
    try:
        # Prepare headers to mimic the browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # Use requests to download
        r = requests.get(url, cookies=session_cookies, headers=headers, stream=True)
        
        # Try to get filename from header
        local_filename = get_filename_from_cd(r.headers.get('content-disposition'))
        if not local_filename:
            local_filename = url.split('/')[-1]
            if "?" in local_filename:
                local_filename = local_filename.split("?")[0]
        
        # Clean filename
        local_filename = os.path.basename(local_filename)
        path = os.path.join(DOWNLOAD_DIR, local_filename)

        # Check if file already exists
        if os.path.exists(path):
            print(f"Skipping {local_filename}, already exists.")
            return True # Treated as success/already done

        print(f"Downloading {local_filename}...")
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

# ... (imports remain the same)

def main():
    # Setup Chrome Options for "stealth"
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # Comment out to see the browser
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--ignore-certificate-errors") # Add this in case of SSL issues

    # Initialize WebDriver
    driver = webdriver.Chrome(options=chrome_options)
    
    # Anti-detection script
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        print(f"Navigating to {BASE_URL}")
        driver.get(BASE_URL)
        
        wait = WebDriverWait(driver, 15)

        # IMPORTANT: The content is inside an IFRAME.
        # We must switch to the iframe to access the elements.
        print("Waiting for iframe...")
        # There seems to be an iframe. Let's find it.
        # Based on subagent investigation, the search is in an iframe.
        # We can switch to it by tag name if it's the only one or prominent
        try:
           iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
           print("Switching to iframe...")
           driver.switch_to.frame(iframe)
        except Exception:
           print("iframe not found, assuming direct content.")

        # Wait for search box
        print("Waiting for search input...")
        search_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="busca2"]')))
        
        print("Entering search term...")
        search_input.clear()
        search_input.send_keys("a")

        # Find and click search button
        # The user said //*[@id="sencillas"]/fieldset/input[3]
        # We verified it exists in the iframe.
        search_button = driver.find_element(By.XPATH, '//*[@id="sencillas"]/fieldset/input[3]')
        search_button.click()

        processed_links = set()

        while True:
            print("Processing results table...")
            # Wait for table to load/reload
            # The table logic: //*[@id="superResultados"]/div/table/tbody
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="superResultados"]/div/table/tbody/tr')))
            
            # Additional small wait to ensure table is fully rendered
            time.sleep(2)

            # Get all rows
            rows = driver.find_elements(By.XPATH, '//*[@id="superResultados"]/div/table/tbody/tr')
            
            # Create a session from selenium cookies for downloading
            session_cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
            
            row_count_in_page = len(rows)
            print(f"Found {row_count_in_page} rows on this page.")

            # Skip the first row if it is a header (usually it is). 
            # The user said to access tr[2], which implies tr[1] is header.
            # We will iterate from index 1 (second row) if multiple rows exist.
            start_index = 1 if row_count_in_page > 1 else 0
            
            # Check if strictly following user instructions (tr[2] start)
            # We will just try to find links in ALL rows to be safe, starting from 1
            
            links_found_on_page = 0
            
            for i in range(start_index, row_count_in_page):
                row = rows[i]
                try:
                    # Attempt to find the specific links relative to the row
                    # User: .//td[5]/a[1] (Transcription) and .//td[5]/a[2] (Audio)
                    
                    try:
                        link1 = row.find_element(By.XPATH, './/td[5]/a[1]')
                        url1 = link1.get_attribute('href')
                        
                        if url1 and url1 not in processed_links:
                            if download_file(url1, session_cookies):
                                processed_links.add(url1)
                            links_found_on_page += 1
                    except Exception:
                        pass # Link 1 not found in this row

                    try:
                        link2 = row.find_element(By.XPATH, './/td[5]/a[2]')
                        url2 = link2.get_attribute('href')
                        
                        if url2 and url2 not in processed_links:
                            if download_file(url2, session_cookies):
                                processed_links.add(url2)
                            links_found_on_page += 1
                    except Exception:
                        pass # Link 2 not found

                except Exception as e:
                    print(f"Error processing row {i}: {e}")
                    continue
            
            print(f"Processed {links_found_on_page} links on this page.")

            # Check for "NEXT" button
            # XPath: //*[@id="superResultados"]/fieldset/a
            # Often there are "Anteriores" and "Siguientes"
            try:
                # Re-fetch elements to avoid staleness
                next_buttons = driver.find_elements(By.XPATH, '//*[@id="superResultados"]/fieldset/a')
                
                next_btn = None
                for btn in next_buttons:
                    text = btn.text.lower()
                    if "siguientes" in text or ">" in text:
                        next_btn = btn
                        break
                
                if next_btn:
                    print("Clicking 'Siguientes'...")
                    driver.execute_script("arguments[0].click();", next_btn)
                    
                    # We need to wait for the table to change. 
                    # Simple wait is usually okay for this kind of site.
                    time.sleep(3)
                else:
                    print("No 'Siguientes' button found. Finished.")
                    break
            except Exception as e:
                print(f"Error finding next button: {e}")
                break

    except Exception as e:
        # Print fuller error
        import traceback
        traceback.print_exc()
        print(f"An error occurred: {e}")
        try:
             print("Current URL:", driver.current_url)
        except: pass
    finally:
        print("Closing driver...")
        driver.quit()

if __name__ == "__main__":
    main()
