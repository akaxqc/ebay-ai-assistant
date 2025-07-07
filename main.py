from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional
import requests
import time
import os
from dotenv import load_dotenv
from base64 import b64encode

# === Load .env credentials ===
load_dotenv()
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_MARKETPLACE_ID = "EBAY_US"

app = FastAPI(title="eBay AI Assistant", version="2.0.0")

# === Global Token Cache ===
access_token_cache = {
    "token": None,
    "expires_at": 0
}

# === OAuth Token Fetcher ===
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

# === Real eBay Price Check Endpoint ===
@app.get("/price-check-live")
def price_check_live(query: str, limit: int = 5):
    token = get_ebay_access_token()

    url = f"https://api.ebay.com/buy/browse/v1/item_summary/search"
    params = {
        "q": query,
        "limit": limit
    }
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

    prices = [float(item["price"]["value"]) for item in items if "price" in item]
    avg_price = round(sum(prices) / len(prices), 2)

    simplified_results = [
        {
            "title": item.get("title"),
            "price": item["price"]["value"],
            "currency": item["price"]["currency"],
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

# === Optional Echo Endpoint for GPT ===
class PromptRequest(BaseModel):
    prompt: str

@app.post("/ask")
def ask_endpoint(data: PromptRequest):
    return {"reply": f"You said: {data.prompt}"}
