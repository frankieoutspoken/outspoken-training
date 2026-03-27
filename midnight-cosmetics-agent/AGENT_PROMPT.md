# Midnight Cosmetics Agent — Build Prompt

> **What is this file?** This is a **markdown** file (`.md`). Markdown is a simple formatting language — you write plain text with symbols like `#` for headings, `**` for bold, `-` for bullet points, and ``` for code blocks. It's how most technical documentation is written, and it's what Claude Code reads natively. This entire prompt is written in markdown so Claude Code can parse the structure cleanly.

---

Build a **Midnight Cosmetics** customer service multi-agent system using the **Claude Agent SDK (Python)** with a **Streamlit** frontend.

## Project Structure

```
midnight-cosmetics-agent/
├── src/
│   ├── __init__.py
│   ├── config.py                  # Environment vars, file paths
│   ├── app.py                     # Streamlit frontend
│   ├── agents/
│   │   ├── __init__.py            # Imports all agents, exports AGENTS dict
│   │   ├── product_agent.py       # Product & FAQ specialist
│   │   ├── returns_agent.py       # Returns specialist
│   │   ├── beauty_agent.py        # Beauty profile generator
│   │   └── escalation_agent.py    # Human escalation handler
│   └── tools/
│       ├── __init__.py
│       ├── product_lookup.py      # CSV lookup for products
│       ├── order_lookup.py        # CSV lookup for orders
│       ├── knowledge_search.py    # OpenAI vector store search
│       └── document_generator.py  # .docx beauty profile generator
├── data/                          # Symlinked or copied from parent repo
├── .env.example
├── requirements.txt
└── CLAUDE.md
```

## Dependencies

```
claude-agent-sdk>=0.1.50
anthropic>=0.52.0
openai>=1.82.0
streamlit>=1.45.0
python-dotenv>=1.0.0
python-docx>=1.1.0
pandas>=2.2.0
numpy>=1.26.0
nest_asyncio>=1.6.0
```

## Environment Variables

```
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
VECTOR_STORE_ID=your_vector_store_id
```

## Config (src/config.py)

Load env vars with `python-dotenv`. Define paths:
- `PROJECT_ROOT` = the `midnight-cosmetics-agent/` directory
- `DATA_DIR` = `../data/` (parent repo's data folder)
- `PRODUCTS_CSV` = `data/midnight_products.csv`
- `ORDERS_CSV` = `data/midnight_orders.csv`
- `RETURN_POLICY` = `data/midnight_return_policy.md`
- `OUTPUT_DIR` = `midnight-cosmetics-agent/output/` (for generated docs, create if not exists)

## Tools

All tools use the `@tool` decorator from `claude_agent_sdk` and are bundled into a single MCP server called `"midnight"` via `create_sdk_mcp_server()`.

### search_products
- **Name**: `search_products`
- **Description**: Search the Midnight Cosmetics product catalog. Filter by category (Face, Eyes, Lips), max price, or search product names and descriptions by keyword.
- **Input schema**: `{"query": str, "category": str, "max_price": float}`
- **Implementation**: Read `data/midnight_products.csv` with pandas. Filter by category (case-insensitive), max_price (if > 0), and keyword search (check if query appears in name OR description, case-insensitive). Return formatted results with name, category, price, and description.

### lookup_order
- **Name**: `lookup_order`
- **Description**: Look up a Midnight Cosmetics order by order ID. Returns customer name, product, order date, delivery date, status, and whether it was a sale item.
- **Input schema**: `{"order_id": str}`
- **Implementation**: Read `data/midnight_orders.csv` with pandas. Match by order_id (case-insensitive). If delivered, calculate days since delivery (`datetime.now() - delivery_date`). Return all order fields plus `days_since_delivery` and `within_7_day_return_window` (Yes/No).

### search_knowledge_base
- **Name**: `search_knowledge_base`
- **Description**: Search the Midnight Cosmetics beauty knowledge base for skincare routines, ingredient info, application tips, and FAQs. Use for beauty advice and how-to questions — NOT for product lookups.
- **Input schema**: `{"query": str}`
- **Implementation**: Use the OpenAI client to call `vector_stores.search()` with `vector_store_id` from env, query text, and `max_num_results=3`. Return the text content of matching chunks.

### generate_beauty_profile
- **Name**: `generate_beauty_profile`
- **Description**: Generate a branded Midnight Cosmetics beauty profile document (.docx). Provide customer name, skin type, preferred look, concerns, and product recommendations as a JSON object.
- **Input schema**: `{"profile_data": str}` (JSON string)
- **Implementation**: Parse the JSON. Use `python-docx` to create a branded document with: title ("Midnight Cosmetics"), subtitle ("Your Personalized Beauty Profile"), customer name, date, skin profile summary, product recommendations with prices and reasons, morning/evening routines, application tips, and a footer. Save to `output/` directory. Return the file path.

## MCP Server Setup

Bundle all 4 tools into one MCP server in `app.py`:

```python
midnight_server = create_sdk_mcp_server(
    name="midnight",
    version="1.0.0",
    tools=[search_products, lookup_order, search_knowledge_base, generate_beauty_profile],
)
```

Tool names become: `mcp__midnight__search_products`, `mcp__midnight__lookup_order`, `mcp__midnight__search_knowledge_base`, `mcp__midnight__generate_beauty_profile`

## Agents

Each agent is its own file in `src/agents/`. Each file exports a single `AgentDefinition` instance. The `__init__.py` imports all four and exports them as a dict called `AGENTS`.

### Router (main agent — defined in app.py system_prompt)
- **Model**: `claude-haiku-4-5-20251001`
- **Role**: Receives all customer messages, delegates to the right specialist
- **System prompt**:
  ```
  You are the Midnight Cosmetics customer service router.
  Your job is to understand the customer's request and delegate to the right specialist agent.

  ROUTING RULES:
  - Product questions, recommendations, skincare tips, ingredient questions, FAQs → use product-agent
  - Return requests, refund questions, order issues, damaged items → use returns-agent
  - Beauty quiz results, personalized profile requests → use beauty-profile-agent
  - Requests for a human, complaints you can't categorize, manager requests → use escalation-agent

  Always delegate. Never try to answer directly — use the right agent.
  ```
- **Allowed tools**: `["Agent", "mcp__midnight__search_products", "mcp__midnight__lookup_order", "mcp__midnight__search_knowledge_base", "mcp__midnight__generate_beauty_profile"]`
- **Permission mode**: `acceptEdits`
- **Max turns**: 15

### product-agent (src/agents/product_agent.py)
- **Model**: `sonnet`
- **Description**: Answer questions about products, ingredients, skincare routines, application tips, and beauty advice.
- **Tools**: `mcp__midnight__search_products`, `mcp__midnight__search_knowledge_base`
- **Instructions**: Knowledgeable beauty consultant. Warm and helpful. Always include product name, price, and relevance. Never recommend products not in the catalog. Never mention competitors. Never give medical advice. Don't make things up.

### returns-agent (src/agents/returns_agent.py)
- **Model**: `sonnet`
- **Description**: Handle return requests, refund questions, order issues, damaged items. Always asks for order ID first.
- **Tools**: `mcp__midnight__lookup_order`
- **Instructions**: Follow the return policy exactly. Process: ask for order ID → look up order → calculate days since delivery → apply rules → respond. The full return policy text from `data/midnight_return_policy.md` is loaded and embedded directly in the prompt via f-string. Guardrails: never override policy, never promise ineligible refunds, be empathetic but firm. If customer disputes → suggest connecting with human team member.

### beauty-profile-agent (src/agents/beauty_agent.py)
- **Model**: `sonnet`
- **Description**: Generate personalized beauty profiles from quiz results.
- **Tools**: `mcp__midnight__search_products`, `mcp__midnight__search_knowledge_base`, `mcp__midnight__generate_beauty_profile`
- **Instructions**: Collect name, skin type, preferred look, concerns (ask if not provided). Search products for 3-5 matches. Search knowledge base for relevant tips. Generate .docx with `generate_beauty_profile` tool — pass a JSON string with: name, skin_type, preferred_look, concerns (list), recommendations (list of {name, price, reason}), morning_routine, evening_routine, tips.

### escalation-agent (src/agents/escalation_agent.py)
- **Model**: `haiku`
- **Description**: Handle situations other agents can't resolve. Collect name and email.
- **Tools**: none
- **Instructions**: Apologize, collect full name and email, confirm back, let them know human follow-up within 24 hours. Never make promises about outcomes.

### agents/__init__.py

```python
from src.agents.product_agent import product_agent
from src.agents.returns_agent import returns_agent
from src.agents.beauty_agent import beauty_agent
from src.agents.escalation_agent import escalation_agent

AGENTS = {
    "product-agent": product_agent,
    "returns-agent": returns_agent,
    "beauty-profile-agent": beauty_agent,
    "escalation-agent": escalation_agent,
}
```

## Streamlit Frontend (src/app.py)

### Session Tracking
- Generate a `session_id` (UUID4) when the chat initializes
- Store in `st.session_state`
- Use the SDK's `session_id` from `ResultMessage` to resume conversations via `ClaudeAgentOptions(resume=session_id)`
- Display session_id in sidebar

### Async Handling
- Wrap async agent calls in a `run_agent_sync()` function
- Use `nest_asyncio` to handle Streamlit's existing event loop
- Try `asyncio.get_running_loop()` first, fall back to `asyncio.run()`

### UI Layout
- Title: "Midnight Cosmetics" with moon emoji
- Chat interface with `st.chat_input`
- Messages show which agent handled them via `st.caption`
- Sidebar shows:
  - Current session ID
  - Current active agent
  - Agent handoff history (e.g., "Router → product-agent → escalation-agent")
  - "New Conversation" button that resets everything

### Message Handling
- Stream `AssistantMessage` content blocks — collect `TextBlock` text
- Track agent routing via `ToolUseBlock` where `block.name == "Agent"` — read `subagent_type` from input
- Capture `session_id` from `ResultMessage` for session resumption
- Only use `ResultMessage.result` as fallback if no text was collected from streaming

## Test Scenarios

| # | Input | Expected |
|---|---|---|
| 1 | "What products do you have for oily skin?" | Routes to product-agent → CSV lookup → finds Stardust Setting Powder |
| 2 | "How do I apply foundation without it looking cakey?" | Routes to product-agent → vector store search → finds application tips |
| 3 | "I want to return order MC-1001" | Routes to returns-agent → order lookup → 3 days since delivery → eligible |
| 4 | "I want to return order MC-1002" | Routes to returns-agent → order lookup → 10 days → past window, denied |
| 5 | "I want to return order MC-1003" | Routes to returns-agent → sale item → final sale, denied |
| 6 | "Order MC-1008 arrived damaged" | Routes to returns-agent → damage exception → full refund offered |
| 7 | "I took the beauty quiz: oily skin, natural look, acne" | Routes to beauty-profile-agent → collects info → generates .docx |
| 8 | "I need to speak to a manager" | Routes to escalation-agent → asks for name and email |
