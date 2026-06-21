from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def scrape_webpage(url: str) -> BeautifulSoup:
    """
    Fetches the content of a webpage using a headless Chromium browser
    and parses it into a BeautifulSoup object. This allows us to read
    modern JavaScript-heavy websites (React, Next.js, etc).
    """
    print(f"Fetching URL with Headless Browser: {url}")
    try:
        with sync_playwright() as p:
            # Launch Chromium in headless mode
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            # Navigate to the URL and wait for all network traffic (Javascript, APIs) to finish
            page.goto(url, wait_until="networkidle", timeout=20000)
            
            # Grab the fully rendered HTML
            html_content = page.content()
            browser.close()
            
            # Parse it with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup
            
    except PlaywrightTimeoutError:
        print(f" -> Error: The connection timed out while trying to reach '{url}'. The website is too slow.")
    except Exception as e:
        print(f" -> Error: An unexpected error occurred while scraping '{url}': {e}")
        
    # If any error occurred, we return None so the main app knows to skip this URL
    return None

def extract_text(soup: BeautifulSoup) -> str:
    """
    Cleans the parsed HTML by removing unwanted elements and extracts meaningful text.
    Includes error handling for empty or heavily-javascript-dependent pages.
    
    Args:
        soup (BeautifulSoup): The parsed HTML document.
        
    Returns:
        str: Cleaned, readable text extracted from the webpage.
    """
    if not soup:
        return ""
        
    # Remove all script, style, header, footer, and nav tags 
    # as they usually contain code, menus, or copyright info, not the core content.
    for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']):
        tag.decompose()
        
    # Extract text from the remaining HTML, using a space to separate elements
    text = soup.get_text(separator=' ')
    
    # Clean up whitespace: break into lines, strip leading/trailing spaces, 
    # and remove empty lines to make it neat.
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    cleaned_text = '\n'.join(chunk for chunk in chunks if chunk)
    
    # Robust check: If the page text is practically empty (e.g. less than 50 characters),
    # it usually means the site requires JavaScript to load its text, or it actively blocked us.
    if len(cleaned_text) < 50:
        print(" -> Warning: Extracted text is suspiciously short. This page might require JavaScript to load, or the main text is hidden.")
        return ""
    
    return cleaned_text

# Simple test block to try out both functions
if __name__ == "__main__":
    # Test a broken URL to see our new error handling in action!
    bad_url = "https://this-website-does-not-exist-12345.com"
    print("Testing bad URL...")
    soup_result = scrape_webpage(bad_url)
    if soup_result is None:
        print("Error handling successfully caught the bad URL!")
