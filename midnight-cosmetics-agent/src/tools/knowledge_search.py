from typing import Any
from openai import OpenAI
from claude_agent_sdk import tool
from src.config import OPENAI_API_KEY, VECTOR_STORE_ID


@tool(
    "search_knowledge_base",
    "Search the Midnight Cosmetics beauty knowledge base for skincare routines, ingredient info, application tips, and FAQs. Use this for beauty advice, how-to questions, and general information — NOT for product lookups.",
    {"query": str},
)
async def search_knowledge_base(args: dict[str, Any]) -> dict[str, Any]:
    query = args.get("query", "")

    if not VECTOR_STORE_ID:
        return {
            "content": [{"type": "text", "text": "Knowledge base not configured. Set VECTOR_STORE_ID in .env."}],
            "is_error": True,
        }

    client = OpenAI(api_key=OPENAI_API_KEY)

    results = client.vector_stores.search(
        vector_store_id=VECTOR_STORE_ID,
        query=query,
        max_num_results=3,
    )

    if not results.data:
        return {"content": [{"type": "text", "text": "No relevant articles found in the knowledge base."}]}

    output = []
    for result in results.data:
        for content in result.content:
            if content.type == "text":
                output.append(content.text)

    return {"content": [{"type": "text", "text": "\n\n---\n\n".join(output)}]}
