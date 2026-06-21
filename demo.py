import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

url = "https://react.dev/learn"

print("==================================================")
print(f"TARGET URL: {url}")
print("==================================================\n")

# --- THE OLD WAY (Requests) ---
print("1. THE OLD WAY (Using Requests)")
print("   (Downloading the raw HTML from the server...)")
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers)
soup_old = BeautifulSoup(response.text, 'html.parser')

# Clean up script tags to see what text we got
for tag in soup_old(['script', 'style', 'noscript']):
    tag.decompose()
old_text = soup_old.get_text(separator=' ').strip()

if len(old_text) < 100:
    print("\n   RESULT: FAILED!")
    print(f"   What Requests saw: '{old_text}'")
    print("   Explanation: The server just sent an empty page because React requires Javascript to build the UI!")
else:
    print(f"   Success! Found {len(old_text)} characters of text.")

print("\n" + "-"*50 + "\n")

# --- THE NEW WAY (Playwright) ---
print("2. THE NEW WAY (Using Playwright)")
print("   (Opening a real invisible Chrome browser and running Javascript...)")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(user_agent="Mozilla/5.0")
    page.goto(url, wait_until="networkidle")
    html_content = page.content()
    browser.close()

soup_new = BeautifulSoup(html_content, 'html.parser')

# Clean up script tags
for tag in soup_new(['script', 'style', 'noscript', 'nav']):
    tag.decompose()
new_text = soup_new.get_text(separator=' ').strip()

print("\n   RESULT: SUCCESS!")
print(f"   What Playwright saw: {len(new_text)} characters of text!")
print(f"   Snippet: '{new_text[:150]}...'")
print("   Explanation: Because Playwright is a real browser, it ran the Javascript, built the UI, and grabbed the actual text!")

print("\n==================================================")
