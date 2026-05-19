import streamlit as st
from woocommerce import API

class WooCommerceClient:
    def __init__(self):
        self.url = st.secrets["woocommerce"]["store_url"]
        self.key = st.secrets["woocommerce"]["consumer_key"]
        self.secret = st.secrets["woocommerce"]["consumer_secret"]
        self.wcapi = API(
            url=self.url,
            consumer_key=self.key,
            consumer_secret=self.secret,
            version="wc/v3",
            timeout=50
        )

    @st.cache_data(ttl=3600)
    def fetch_orders(self, _self, after=None, before=None, status=None):
        """Fetch orders with auto-pagination."""
        params = {
            "per_page": 100,
            "page": 1
        }
        if after:
            params["after"] = after
        if before:
            params["before"] = before
        if status:
            params["status"] = status

        all_orders = []
        while True:
            response = self.wcapi.get("orders", params=params)
            if response.status_code != 200:
                break
            
            orders = response.json()
            if not orders:
                break
            
            all_orders.extend(orders)
            
            # Check for next page
            total_pages = int(response.headers.get('X-WP-TotalPages', 1))
            if params["page"] >= total_pages:
                break
            params["page"] += 1
            
        return all_orders

    @st.cache_data(ttl=86400)
    def fetch_products(self, _self):
        """Fetch all products for categories and SKUs."""
        params = {"per_page": 100, "page": 1}
        all_products = []
        while True:
            response = self.wcapi.get("products", params=params)
            if response.status_code != 200:
                break
            products = response.json()
            if not products:
                break
            all_products.extend(products)
            total_pages = int(response.headers.get('X-WP-TotalPages', 1))
            if params["page"] >= total_pages:
                break
            params["page"] += 1
        return all_products

    @st.cache_data(ttl=86400)
    def fetch_categories(self, _self):
        """Fetch all categories."""
        params = {"per_page": 100, "page": 1}
        all_cats = []
        while True:
            response = self.wcapi.get("products/categories", params=params)
            if response.status_code != 200:
                break
            cats = response.json()
            if not cats:
                break
            all_cats.extend(cats)
            total_pages = int(response.headers.get('X-WP-TotalPages', 1))
            if params["page"] >= total_pages:
                break
            params["page"] += 1
        return all_cats
