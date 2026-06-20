import requests
from bs4 import BeautifulSoup

def scrape_webpage(url: str) -> BeautifulSoup:
    """
    Fetches the content of a webpage and parses it into a BeautifulSoup object.
    Includes robust error handling for various network failures.
    
    Args:
        url (str): The web address to scrape.
        
    Returns:
        BeautifulSoup: A parsed representation of the HTML document, or None if it fails.
    """
    print(f"Fetching URL: {url}")
    try:
        # We use a User-Agent header so the website doesn't block us thinking we're a spam bot.
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        # Make an HTTP GET request to download the page content. We also set a 10-second timeout.
        response = requests.get(url, headers=headers, timeout=10)
        
        # Raise an exception if the server returned an error (like 404 Not Found or 500 Internal Error)
        response.raise_for_status()
        
        # Robust check: Make sure the URL actually returned an HTML webpage, not a PDF or an Image.
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' not in content_type:
            print(f" -> Warning: Expected HTML but got '{content_type}'. This URL might be a file or image.")
            return None
            
        # Parse the raw HTML text into a structured BeautifulSoup object
        soup = BeautifulSoup(response.text, 'html.parser')
        
        return soup

    # Catch specific network errors so we can tell the user exactly what went wrong
    except requests.exceptions.Timeout:
        print(f" -> Error: The connection timed out while trying to reach '{url}'. The website is too slow.")
    except requests.exceptions.HTTPError as e:
        print(f" -> Error: The website returned an HTTP error (e.g., 404 or 403 Forbidden): {e}")
    except requests.exceptions.ConnectionError:
        print(f" -> Error: Failed to connect. Is the URL typed correctly? '{url}'")
    except requests.exceptions.MissingSchema:
        print(f" -> Error: Invalid URL format. Did you forget 'http://' or 'https://' for '{url}'?")
    except requests.exceptions.RequestException as e:
        # Catch-all for any other network issues
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
