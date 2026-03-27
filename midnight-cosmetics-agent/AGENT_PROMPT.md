# Midnight Cosmetics Agent — Build Prompt

> **What is this file?** This is a **markdown** file (`.md`). Markdown is a simple formatting language — you write plain text with symbols like `#` for headings, `**` for bold, `-` for bullet points, and ``` for code blocks. It's how most technical documentation is written, and it's what Claude Code reads natively. This entire prompt is written in markdown so Claude Code can parse the structure cleanly.

---

Use the `/new-sdk-app` skill to scaffold the project, then build the following multi-agent system.

## Overview

Build a **Midnight Cosmetics** customer service multi-agent system using the **Claude Agent SDK (Python)** with a **Streamlit** frontend.

Follow the project structure defined in `CLAUDE.md`.

## Agent Architecture

### Router Agent
- **Model**: `claude-haiku-4-5-20251001` (fast and cheap — routing is a classification task)
- **Purpose**: Receives all incoming customer messages and routes to the correct specialist agent
- **Routing categories**:
  - `product` — questions about products, ingredients, prices, recommendations, skincare tips, beauty advice
  - `returns` — return requests, order issues, refund questions, damaged items
  - `beauty_profile` — quiz results, personalized recommendations, beauty profile generation
  - `escalation` — requests for a human, complaints, anything the router can't categorize
- **Parameters**: `max_tokens: 50`, `temperature: 0` (deterministic routing)
- **Output format**: JSON with `{"route": "product|returns|beauty_profile|escalation", "reason": "brief explanation"}`
- **Session tracking**: Every interaction must carry a `session_id` (UUID generated at conversation start). Pass this to all specialist agents so the full conversation can be reconstructed.

### Product & FAQ Agent
- **Model**: `claude-sonnet-4-6-20250514`
- **Purpose**: Answer product questions and beauty/skincare advice
- **Instructions**:
  - You are a knowledgeable beauty consultant for Midnight Cosmetics.
  - Be warm, helpful, and enthusiastic about the products without being pushy.
  - When recommending products, always include the product name, price, and why it's relevant to the customer's needs.
  - Never recommend or mention products that aren't in the catalog.
  - If you don't know the answer, say so — don't make things up.
- **Tools**:
  1. `search_products(query: str, category: str = None, max_price: float = None) -> list` — CSV lookup against `data/midnight_products.csv`. Filter by category (Face, Eyes, Lips) and/or max price. Search product names and descriptions.
  2. `search_knowledge_base(query: str) -> list` — Search the OpenAI vector store (ID: `<VECTOR_STORE_ID>`) for relevant beauty articles, skincare tips, ingredient info, and FAQs. Use model `text-embedding-3-small` for query embedding.
- **Parameters**: `max_tokens: 500`, `temperature: 0.3`
- **Guardrails**:
  - Never mention competitor brands
  - Never provide medical advice — redirect to a dermatologist if someone asks about skin conditions
  - Only recommend products from the Midnight Cosmetics catalog

### Returns Agent
- **Model**: `claude-sonnet-4-6-20250514`
- **Purpose**: Handle return requests according to the return policy
- **Instructions**:
  - You handle returns for Midnight Cosmetics.
  - Always ask for the **order ID** first before doing anything.
  - After looking up the order, check ALL of the following rules:

  **RETURN POLICY (follow exactly):**
  - Returns accepted within **7 days** of delivery date only.
  - Items must be **unopened** and in original packaging for a full refund.
  - **Opened items** can only be exchanged for the same product in a different shade — not refunded.
  - **Sale items** are final sale — no returns or exchanges.
  - **Damaged items** receive a full refund regardless of all other rules. Ask for a photo.
  - Refunds processed to original payment method within 5-7 business days.

  **PROCESS:**
  1. Ask for order ID
  2. Look up the order using the order lookup tool
  3. Calculate days since delivery (today's date minus delivery_date)
  4. Check: Is it within 7 days? Is it a sale item? Is it damaged?
  5. Respond according to the rules
  6. If the customer disputes or asks for a manager → hand off to Escalation Agent

- **Tools**:
  1. `lookup_order(order_id: str) -> dict` — CSV lookup against `data/midnight_orders.csv`. Returns order details including customer name, product, order_date, delivery_date, status, and sale_item flag.
- **Parameters**: `max_tokens: 400`, `temperature: 0.1` (low creativity — follow the rules)
- **Guardrails**:
  - Never override the return policy
  - Never promise a refund that doesn't meet the criteria
  - Always be empathetic but firm
- **Handoff**: If the customer is unhappy with the policy decision or asks for a manager, hand off to the Escalation Agent with context about what happened.

### Beauty Profile Agent
- **Model**: `claude-sonnet-4-6-20250514`
- **Purpose**: Generate personalized beauty profile documents from quiz results
- **Instructions**:
  - Collect the following from the customer (ask if not provided):
    - Skin type (oily, dry, combination, sensitive, normal)
    - Preferred look (natural, bold, glam, minimalist)
    - Top skin concerns (acne, aging, dryness, redness, dark spots, pores)
  - Use the product catalog to recommend 3-5 products tailored to their profile
  - Generate a branded beauty profile document (.docx) with:
    - Customer's name (ask for it)
    - Their skin profile summary
    - Personalized product recommendations with explanations
    - A morning and evening routine suggestion
    - Application tips relevant to their concerns
  - Use the Midnight Cosmetics brand voice: warm, confident, inclusive
- **Tools**:
  1. `search_products(query: str, category: str = None) -> list` — same product lookup tool
  2. `search_knowledge_base(query: str) -> list` — for skincare tips and routines relevant to their profile
  3. `generate_document(content: dict) -> str` — creates a branded .docx file and returns the file path
- **Parameters**: `max_tokens: 1000`, `temperature: 0.5` (some creativity for personalized writing)

### Escalation Agent
- **Model**: `claude-haiku-4-5-20251001` (simple task — just collect info)
- **Purpose**: Handle situations other agents can't resolve
- **Instructions**:
  - Apologize that you couldn't resolve their issue
  - Collect the customer's **full name** and **email address**
  - Confirm the information back to them
  - Let them know a human team member will follow up within 24 hours
  - Log the escalation with: session_id, customer name, email, reason for escalation, conversation summary
- **Parameters**: `max_tokens: 200`, `temperature: 0`
- **Guardrails**:
  - Never make promises about outcomes ("I'm sure they'll approve your refund")
  - Just collect info and confirm

## Session Tracking

Every conversation starts with a `session_id` (UUID4). This ID:
- Gets generated when the Streamlit chat initializes
- Gets passed to every agent interaction
- Gets logged with every tool call
- Allows the full conversation to be reconstructed: which agents handled what, what tools were called, what decisions were made
- Display the session_id in the Streamlit sidebar

## Streamlit Frontend

- Chat interface with message history
- Sidebar showing:
  - Current session ID
  - Which agent is currently handling the conversation
  - Agent handoff history (e.g., "Router → Product Agent → Escalation Agent")
- Messages from different agents should be visually distinct (different colors or labels)
- Include a "New Conversation" button that generates a fresh session_id

## Environment Variables

```
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
VECTOR_STORE_ID=your_vector_store_id
```

## Test Scenarios to Verify

After building, test these:

1. **Product lookup**: "What products do you have for oily skin?" → CSV lookup, should find Stardust Setting Powder and others
2. **Knowledge base (RAG)**: "How do I apply foundation without it looking cakey?" → Vector store search, finds application tips article
3. **Return within window**: "I want to return order MC-1001" → 3 days since delivery, eligible
4. **Return outside window**: "I want to return order MC-1002" → 10 days since delivery, should deny
5. **Sale item return**: "I want to return order MC-1003" → Sale item, final sale, should deny
6. **Damaged item**: "Order MC-1008 arrived damaged" → Should offer full refund regardless of window
7. **Beauty profile**: "I took the beauty quiz: oily skin, natural look, acne concerns" → Should generate personalized doc
8. **Escalation**: "I need to speak to a manager" → Should collect name and email
9. **Session continuity**: Verify the session_id persists across agent handoffs
