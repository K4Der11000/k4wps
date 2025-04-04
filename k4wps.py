import requests
import cloudscraper
from bs4 import BeautifulSoup
import re
import json
import random
from PIL import Image
import time

# مصادر البروكسيات المجانية (يمكنك تغييرها أو إضافة أخرى)
PROXY_SOURCES = [
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
]

# قائمة البروكسيات
PROXIES_LIST = []

# تحديث قائمة البروكسيات
def update_proxies():
    global PROXIES_LIST
    new_proxies = []
    
    print("[+] تحديث قائمة البروكسيات...")
    
    for url in PROXY_SOURCES:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                proxy_list = response.text.strip().split("\n")
                new_proxies.extend(proxy_list)
        except requests.RequestException as e:
            print(f"[!] تعذر جلب البروكسيات من {url}: {e}")
    
    # تصفية البروكسيات الصالحة
    PROXIES_LIST = validate_proxies(new_proxies)
    print(f"[+] تم تحديث قائمة البروكسيات ({len(PROXIES_LIST)} بروكسي صالح).")

# التحقق من صلاحية البروكسيات
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

# اختيار بروكسي عشوائي
def get_random_proxy():
    if not PROXIES_LIST:
        update_proxies()
    return {"http": f"http://{random.choice(PROXIES_LIST)}", "https": f"http://{random.choice(PROXIES_LIST)}"}

# عرض البانر عند تشغيل السكريبت
def show_banner():
    try:
        banner_path = "banner.jpg"
        img = Image.open(banner_path)
        img.show()
    except Exception as e:
        print(f"[!] تعذر عرض البانر: {e}")

# تشغيل عرض البانر
show_banner()

# تحميل قاعدة بيانات الثغرات
def load_vulnerabilities():
    try:
        with open("wp_vulnerabilities.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print("[!] لم يتم العثور على قاعدة بيانات الثغرات!")
        return {}

# فحص موقع WordPress باستخدام Cloudscraper والبروكسيات
def check_wordpress(url):
    if not url.startswith("http"):
        url = "http://" + url

    results = {"url": url, "plugins": [], "themes": []}

    try:
        scraper = cloudscraper.create_scraper()  # إنشاء متصفح وهمي لتجاوز Cloudflare
        proxy = get_random_proxy()  # اختيار بروكسي عشوائي
        print(f"[+] استخدام البروكسي: {proxy['http']}")

        response = scraper.get(url, proxies=proxy, timeout=10)
        if response.status_code != 200:
            print(f"[!] تعذر الوصول إلى الموقع: {url}")
            return

        # التحقق مما إذا كان الموقع يستخدم WordPress
        if "wp-content" in response.text or "wp-includes" in response.text:
            print(f"[+] الموقع {url} يعمل بـ WordPress.")
        else:
            print(f"[-] الموقع {url} لا يبدو أنه يعمل بـ WordPress.")
            return

        # استخراج إصدار WordPress
        soup = BeautifulSoup(response.text, "html.parser")
        generator = soup.find("meta", {"name": "generator"})
        if generator and "WordPress" in generator.get("content", ""):
            wp_version = generator["content"].split("WordPress ")[-1]
            results["version"] = wp_version
            print(f"[+] إصدار WordPress: {wp_version}")

        # البحث عن الإضافات
        print("\n[+] البحث عن الإضافات المثبتة:")
        plugins = re.findall(r'/wp-content/plugins/([a-zA-Z0-9-_]+)/', response.text)
        results["plugins"] = list(set(plugins))
        for plugin in results["plugins"]:
            print(f"  - {plugin}")

        # البحث عن القوالب
        print("\n[+] البحث عن القوالب المثبتة:")
        themes = re.findall(r'/wp-content/themes/([a-zA-Z0-9-_]+)/', response.text)
        results["themes"] = list(set(themes))
        for theme in results["themes"]:
            print(f"  - {theme}")

    except requests.RequestException as e:
        print(f"[!] خطأ أثناء الاتصال بالموقع: {e}")

# تحديث البروكسيات تلقائيًا كل فترة
def auto_update_proxies(interval=300):
    while True:
        update_proxies()
        time.sleep(interval)

# تشغيل التحديث التلقائي للبروكسيات في خلفية السكريبت
import threading
threading.Thread(target=auto_update_proxies, daemon=True).start()

# تشغيل الفحص
target_url = input("أدخل رابط الموقع: ")
check_wordpress(target_url)
