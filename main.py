from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID", "DanyAziz-akaxqc-PRD-8ca4033b2-3ebe98a8")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET", "PRD-8e9abf40e836-f10b-43b4-ac6c-a370")

# Encode credentials
import base64
BASIC_AUTH = base64.b64encode(f"{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}".encode()).decode()

def get_ebay_access_token():
    url = "https://api.ebay.com/identity/v1/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {BASIC_AUTH}"
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code != 200:
        print("🔴 Token request failed:", response.status_code, response.text)
        response.raise_for_status()

    access_token = response.json().get("access_token")
    print("🟢 Access token retrieved.")
    return access_token

@app.get("/")
def root():
    return {"message": "eBay AI Backend is running."}

@app.get("/price-check-live")
def price_check_live(query: str = "iphone", limit: int = 5):
    try:
        token = get_ebay_access_token()
    except Exception as e:
        return {"error": "Token retrieval failed", "details": str(e)}

    # 🔧 MOCK RESPONSE (until buy.browse scope is approved)
    return {
        "query": query,
        "results": [
            {
                "title": f"{query} - Example Item {i+1}",
                "price": f"${100 + i * 10}",
                "url": "https://www.ebay.com/",
                "condition": "Used",
                "location": "USA"
            } for i in range(limit)
        ],
        "note": "Mock results shown. Live data will appear after scope approval."
    }