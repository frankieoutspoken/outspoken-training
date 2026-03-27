import pandas as pd
from typing import Any
from claude_agent_sdk import tool
from src.config import PRODUCTS_CSV


@tool(
    "search_products",
    "Search the Midnight Cosmetics product catalog. Filter by category (Face, Eyes, Lips), max price, or search product names and descriptions by keyword.",
    {"query": str, "category": str, "max_price": float},
)
async def search_products(args: dict[str, Any]) -> dict[str, Any]:
    df = pd.read_csv(PRODUCTS_CSV)

    query = args.get("query", "").lower()
    category = args.get("category", "")
    max_price = args.get("max_price", 0)

    if category:
        df = df[df["category"].str.lower() == category.lower()]

    if max_price and max_price > 0:
        df = df[df["price"] <= max_price]

    if query:
        mask = (
            df["name"].str.lower().str.contains(query, na=False)
            | df["description"].str.lower().str.contains(query, na=False)
        )
        df = df[mask]

    if df.empty:
        return {"content": [{"type": "text", "text": "No products found matching your criteria."}]}

    results = []
    for _, row in df.iterrows():
        results.append(f"**{row['name']}** ({row['category']}, ${row['price']})\n{row['description']}")

    return {"content": [{"type": "text", "text": "\n\n".join(results)}]}
