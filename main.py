from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional
import requests
import time
import os
from dotenv import load_dotenv
from base64 import b64encode

# === Load credentials from .env ===
load_dotenv()
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_MARKETPLACE_ID = "EBAY_US"

app = FastAPI(title="eBay AI Assistant", version="2.0.0")

# === Global token cache ===
access_token_cache = {
    "token": None,
    "expires_at": 0
}

# === Root route (prevents 404 on Render home) ===
@app.get("/")
def root():
    return {"status": "🟢 eBay AI Backend is running."}

# === OAuth: get eBay access token ===
def get_ebay_access_token():
    if time.time() < access_token_cache["expires_at"]:
        return access_token_cache["token"]

    token_url = "https://api.ebay.com/identity/v1/oauth2/token"
    credentials = f"{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}"
    encoded_credentials = b64encode(credentials.encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}"
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/buy.browse"
    }

    response = requests.post(token_url, headers=headers, data=data)
    response.raise_for_status()
    result = response.json()

    access_token_cache["token"] = result["access_token"]
    access_token_cache["expires_at"] = time.time() + int(result["expires_in"]) - 60

    return result["access_token"]

# === Price Check Endpoint (live listings only) ===
@app.get("/price-check-live", operation_id="price_check_live")
def price_check_live(query: str = Query(..., description="Search term"), limit: int = Query(5, ge=1, le=20)):
    token = get_ebay_access_token()

    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    params = {"q": query, "limit": limit}
    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": EBAY_MARKETPLACE_ID,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    items = response.json().get("itemSummaries", [])

    if not items:
        return {"query": query, "message": "No results found."}

    prices = []
    for item in items:
        try:
            value = float(item.get("price", {}).get("value", 0))
            prices.append(value)
        except (ValueError, TypeError):
            continue

    if not prices:
        return {"query": query, "message": "No valid prices found."}

    avg_price = round(sum(prices) / len(prices), 2)

    simplified_results = [
        {
            "title": item.get("title"),
            "price": item.get("price", {}).get("value"),
            "currency": item.get("price", {}).get("currency"),
            "url": item.get("itemWebUrl")
        }
        for item in items
    ]

    return {
        "query": query,
        "results_found": len(items),
        "average_price": avg_price,
        "lowest_price": min(prices),
        "highest_price": max(prices),
        "items": simplified_results
    }

# === Optional echo endpoint for GPT testing ===
class PromptRequest(BaseModel):
    prompt: str

@app.post("/ask", operation_id="ask_endpoint")
def ask_endpoint(data: PromptRequest):
    return {"reply": f"You said: {data.prompt}"}