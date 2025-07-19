import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import io

# Setup browser headers
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# Extract item ID from URL
def extract_item_id(url):
    match = re.search(r"/itm/(\d+)", url)
    return match.group(1) if match else "Unknown"

# Fetch eBay item data from HTML page
def fetch_ebay_item_data(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "lxml")

        item_id = extract_item_id(url)

        # === PRICE ===
        price = "N/A"
        price_tag = soup.select_one('[itemprop="price"]')
        if price_tag and price_tag.has_attr("content"):
            price = price_tag["content"]
        else:
            possible_price_tags = soup.find_all(string=re.compile(r"\$\d[\d,]*(\.\d{2})?"))
            for tag in possible_price_tags:
                price_match = re.search(r"\$\d[\d,]*(\.\d{2})?", tag)
                if price_match:
                    price = price_match.group()
                    break

        # === SHIPPING ===
        shipping = "N/A"
        shipping_tag = soup.find("span", string=re.compile("Shipping", re.IGNORECASE))
        if shipping_tag:
            next_span = shipping_tag.find_next("span")
            if next_span:
                shipping = next_span.text.strip()

        # === INVENTORY ===
        inventory = "N/A"
        inventory_tag = soup.find("span", class_="qtyTxt") or soup.find("span", string=re.compile("available", re.IGNORECASE))
        if inventory_tag:
            inventory = inventory_tag.text.strip()

        return {
            "item_id": item_id,
            "price": price,
            "shipping": shipping,
            "inventory": inventory
        }

    except Exception as e:
        return {
            "item_id": "N/A",
            "price": "N/A",
            "shipping": "N/A",
            "inventory": "N/A"
        }

# App UI
st.set_page_config(page_title="eBay Item Scraper", layout="centered")
st.title("🛒 eBay Item Info Scraper")
st.write("Upload a `.txt` or `.xlsx` file with eBay item URLs.")

uploaded_file = st.file_uploader("Upload TXT or Excel file", type=["txt", "xlsx"])

if uploaded_file:
    # Read links
    if uploaded_file.name.endswith(".txt"):
        links = uploaded_file.getvalue().decode().splitlines()
    else:
        df_file = pd.read_excel(uploaded_file)
        links = df_file.iloc[:, 0].dropna().tolist()

    st.success(f"✅ Loaded {len(links)} links")

    if st.button("🔍 Start Scraping"):
        results = []
        progress = st.progress(0)
        status = st.empty()

        for i, url in enumerate(links):
            data = fetch_ebay_item_data(url)
            results.append(data)
            progress.progress((i + 1) / len(links))
            status.text(f"Processed {i + 1} of {len(links)}")

        df = pd.DataFrame(results)
        st.subheader("📄 Results")
        st.dataframe(df)

        # Save both formats
        df.to_excel("ebay_results.xlsx", index=False)
        df.to_csv("ebay_results.csv", index=False)

        # Download buttons
        st.download_button("⬇ Download Excel", data=open("ebay_results.xlsx", "rb"), file_name="ebay_results.xlsx")
        st.download_button("⬇ Download CSV", data=open("ebay_results.csv", "rb"), file_name="ebay_results.csv")
