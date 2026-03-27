import pandas as pd
from typing import Any
from datetime import datetime
from claude_agent_sdk import tool
from src.config import ORDERS_CSV


@tool(
    "lookup_order",
    "Look up a Midnight Cosmetics order by order ID. Returns customer name, product, order date, delivery date, status, and whether it was a sale item.",
    {"order_id": str},
)
async def lookup_order(args: dict[str, Any]) -> dict[str, Any]:
    order_id = args.get("order_id", "").strip().upper()
    df = pd.read_csv(ORDERS_CSV)

    match = df[df["order_id"].str.upper() == order_id]

    if match.empty:
        return {"content": [{"type": "text", "text": f"No order found with ID: {order_id}"}]}

    order = match.iloc[0]
    today = datetime.now().strftime("%Y-%m-%d")

    # Calculate days since delivery if delivered
    days_since_delivery = None
    if order["status"] == "Delivered" and pd.notna(order["delivery_date"]) and order["delivery_date"] != "pending":
        delivery = datetime.strptime(order["delivery_date"], "%Y-%m-%d")
        days_since_delivery = (datetime.now() - delivery).days

    result = (
        f"**Order {order['order_id']}**\n"
        f"- Customer: {order['customer']}\n"
        f"- Email: {order['email']}\n"
        f"- Product: {order['product']}\n"
        f"- Price: ${order['price']}\n"
        f"- Order Date: {order['order_date']}\n"
        f"- Delivery Date: {order['delivery_date']}\n"
        f"- Status: {order['status']}\n"
        f"- Sale Item: {order['sale_item']}\n"
        f"- Today's Date: {today}\n"
    )

    if days_since_delivery is not None:
        result += f"- Days Since Delivery: {days_since_delivery}\n"
        result += f"- Within 7-Day Return Window: {'Yes' if days_since_delivery <= 7 else 'No'}\n"

    return {"content": [{"type": "text", "text": result}]}
