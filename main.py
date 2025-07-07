from fastapi import FastAPI, Query
from typing import Optional

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Your GPT-powered eBay Assistant is running!"}

@app.get("/hello")
def say_hello(name: str = "there"):
    return {"message": f"Hello, {name}!"}

@app.get("/fake_ebay_search")
def fake_ebay_search(
    query: str,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
):
    sample_database = {
        "iphone 14": [
            {"title": "iPhone 14 - 128GB - Unlocked", "price": 329.99, "category": "electronics"},
            {"title": "iPhone 14 - Like New", "price": 349.00, "category": "electronics"},
            {"title": "iPhone 14 Black", "price": 341.99, "category": "electronics"}
        ],
        "airpods": [
            {"title": "AirPods Pro - Gen 2", "price": 179.99, "category": "electronics"},
            {"title": "Apple AirPods - New", "price": 129.00, "category": "electronics"},
            {"title": "Used AirPods Gen 1", "price": 89.99, "category": "electronics"}
        ],
        "jordans": [
            {"title": "Jordan 1 Retro High OG", "price": 210.00, "category": "shoes"},
            {"title": "Jordan 4 Thunder", "price": 235.00, "category": "shoes"},
            {"title": "Jordan 11 Low", "price": 199.99, "category": "shoes"}
        ]
    }

    results = sample_database.get(query.lower(), [])
    
    # Apply optional filters
    filtered_results = [
        item for item in results
        if (category is None or item["category"] == category)
        and (min_price is None or item["price"] >= min_price)
        and (max_price is None or item["price"] <= max_price)
    ]

    if not filtered_results:
        return {
            "query": query,
            "message": "No matching items found with current filters."
        }

    average_price = sum(item["price"] for item in filtered_results) / len(filtered_results)

    return {
        "query": query,
        "category": category or "any",
        "min_price": min_price,
        "max_price": max_price,
        "average_price": round(average_price, 2),
        "items_found": len(filtered_results),
        "results": filtered_results
    }
    