import requests
import cloudscraper
from bs4 import BeautifulSoup
import re
import json
import random
from PIL import Image
import time
import threading

# Free proxy sources (you can change or add more)
PROXY_SOURCES = [
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
]

# Proxy list
PROXIES_LIST = []

# Update proxy list
def update_proxies():
    global PROXIES_LIST
    new_proxies = []
    
    print("[+] Updating proxy list...")
    
    for url in PROXY_SOURCES:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                proxy_list = response.text.strip().split("\n")
                new_proxies.extend(proxy_list)
        except requests.RequestException as e:
            print(f"[!] Failed to fetch proxies from {url}: {e}")
    
    # Filter valid proxies
    PROXIES_LIST = validate_proxies(new_proxies)
    print(f"[+] Proxy list updated ({len(PROXIES_LIST)} valid proxies).")

# Validate proxies
def validate_proxies(proxies):
    valid_proxies = []
    test_url = "http://www.google.com"
    
    for proxy in proxies:
        proxy_dict = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        try:
            response = requests.get(test_url, proxies=proxy_dict, timeout=5)
            if response.status_code == 200:
                valid_proxies.append(proxy)
        except:
            continue
    
    return valid_proxies

# Get a random proxy
def get_random_proxy():
    if not PROXIES_LIST:
        update_proxies()
    return {"http": f"http://{random.choice(PROXIES_LIST)}", "https": f"http://{random.choice(PROXIES_LIST)}"}

# Show banner when script runs
def show_banner():
    try:
        banner_path = "banner.jpg"
        img = Image.open(banner_path)
        img.show()
    except Exception as e:
        print(f"[!] Failed to display banner: {e}")

# Run banner display
show_banner()

# Load vulnerability database
def load_vulnerabilities():
    try:
        with open("wp_vulnerabilities.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print("[!] Vulnerability database not found!")
        return {}

# Check WordPress site using Cloudscraper and proxies
def check_wordpress(url):
    if not url.startswith("http"):
        url = "http://" + url

    results = {"url": url, "plugins": [], "themes": []}

    try:
        scraper = cloudscraper.create_scraper()  # Create fake browser to bypass Cloudflare
        proxy = get_random_proxy()  # Select random proxy
        print(f"[+] Using proxy: {proxy['http']}")

        response = scraper.get(url, proxies=proxy, timeout=10)
        if response.status_code != 200:
            print(f"[!] Failed to access site: {url}")
            return

        # Check if site uses WordPress
        if "wp-content" in response.text or "wp-includes" in response.text:
            print(f"[+] The site {url} is using WordPress.")
        else:
            print(f"[-] The site {url} does not appear to be using WordPress.")
            return

        # Extract WordPress version
        soup = BeautifulSoup(response.text, "html.parser")
        generator = soup.find("meta", {"name": "generator"})
        if generator and "WordPress" in generator.get("content", ""):
            wp_version = generator["content"].split("WordPress ")[-1]
            results["version"] = wp_version
            print(f"[+] WordPress version: {wp_version}")

        # Search for installed plugins
        print("\n[+] Searching for installed plugins:")
        plugins = re.findall(r'/wp-content/plugins/([a-zA-Z0-9-_]+)/', response.text)
        results["plugins"] = list(set(plugins))
        for plugin in results["plugins"]:
            print(f"  - {plugin}")

        # Search for installed themes
        print("\n[+] Searching for installed themes:")
        themes = re.findall(r'/wp-content/themes/([a-zA-Z0-9-_]+)/', response.text)
        results["themes"] = list(set(themes))
        for theme in results["themes"]:
            print(f"  - {theme}")

    except requests.RequestException as e:
        print(f"[!] Error connecting to site: {e}")

# Auto-update proxies periodically
def auto_update_proxies(interval=300):
    while True:
        update_proxies()
        time.sleep(interval)

# Start background proxy updater
threading.Thread(target=auto_update_proxies, daemon=True).start()

# Start scanning
target_url = input("Enter site URL: ")
check_wordpress(target_url)
