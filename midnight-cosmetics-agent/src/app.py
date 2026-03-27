import asyncio
import uuid
import streamlit as st
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
)
from src.config import PROJECT_ROOT
from src.tools.product_lookup import search_products
from src.tools.order_lookup import lookup_order
from src.tools.knowledge_search import search_knowledge_base
from src.tools.document_generator import generate_beauty_profile
from src.agents import AGENTS

# --- MCP Server with all custom tools ---
midnight_server = create_sdk_mcp_server(
    name="midnight",
    version="1.0.0",
    tools=[search_products, lookup_order, search_knowledge_base, generate_beauty_profile],
)

# --- Agent Options ---
def get_options(session_id: str | None = None) -> ClaudeAgentOptions:
    opts = ClaudeAgentOptions(
        system_prompt=(
            "You are the Midnight Cosmetics customer service router. "
            "Your job is to understand the customer's request and delegate to the right specialist agent.\n\n"
            "ROUTING RULES:\n"
            "- Product questions, recommendations, skincare tips, ingredient questions, FAQs → use product-agent\n"
            "- Return requests, refund questions, order issues, damaged items → use returns-agent\n"
            "- Beauty quiz results, personalized profile requests → use beauty-profile-agent\n"
            "- Requests for a human, complaints you can't categorize, manager requests → use escalation-agent\n\n"
            "Always delegate. Never try to answer directly — use the right agent."
        ),
        mcp_servers={"midnight": midnight_server},
        agents=AGENTS,
        allowed_tools=[
            "Agent",
            "mcp__midnight__search_products",
            "mcp__midnight__lookup_order",
            "mcp__midnight__search_knowledge_base",
            "mcp__midnight__generate_beauty_profile",
        ],
        permission_mode="acceptEdits",
        model="claude-haiku-4-5-20251001",
        max_turns=15,
        cwd=str(PROJECT_ROOT),
    )

    if session_id:
        opts.resume = session_id

    return opts


def run_agent_sync(prompt: str, session_id: str | None = None) -> tuple[str, str, str | None]:
    """Run the agent and return (response_text, active_agent, sdk_session_id)."""

    response_text = ""
    active_agent = "Router"
    sdk_session_id = None

    async def _run():
        nonlocal response_text, active_agent, sdk_session_id

        options = get_options(session_id)

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_text += block.text
                        elif isinstance(block, ToolUseBlock):
                            if block.name == "Agent":
                                agent_type = block.input.get("subagent_type", "")
                                if agent_type:
                                    active_agent = agent_type

                elif isinstance(message, ResultMessage):
                    sdk_session_id = message.session_id
                    # Only use result as fallback if we didn't get text from streaming
                    if not response_text and message.result:
                        response_text = message.result

    # Handle Streamlit's existing event loop
    try:
        loop = asyncio.get_running_loop()
        import nest_asyncio
        nest_asyncio.apply()
        loop.run_until_complete(_run())
    except RuntimeError:
        asyncio.run(_run())

    return response_text, active_agent, sdk_session_id


# --- Streamlit UI ---
st.set_page_config(page_title="Midnight Cosmetics", page_icon="🌙", layout="wide")

st.title("🌙 Midnight Cosmetics")
st.caption("Customer Service Agent")

# Sidebar
with st.sidebar:
    st.header("Session Info")

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.agent_history = []
        st.session_state.current_agent = "Router"
        st.session_state.sdk_session_id = None

    st.code(st.session_state.session_id, language=None)
    st.caption("Session ID")

    st.divider()
    st.subheader("Current Agent")
    st.info(st.session_state.current_agent)

    if st.session_state.agent_history:
        st.subheader("Agent History")
        st.text(" → ".join(st.session_state.agent_history))

    st.divider()
    if st.button("New Conversation", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.agent_history = []
        st.session_state.current_agent = "Router"
        st.session_state.sdk_session_id = None
        st.rerun()

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("agent"):
            st.caption(f"Handled by: {msg['agent']}")

# Chat input
if prompt := st.chat_input("How can we help you today?"):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Run agent
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_text, active_agent, sdk_session_id = run_agent_sync(
                prompt, st.session_state.sdk_session_id
            )

            # Update session state
            st.session_state.current_agent = active_agent
            if sdk_session_id:
                st.session_state.sdk_session_id = sdk_session_id
            if active_agent not in st.session_state.agent_history:
                st.session_state.agent_history.append(active_agent)

            if response_text:
                st.markdown(response_text)
                st.caption(f"Handled by: {active_agent}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "agent": active_agent,
                })
            else:
                fallback = "I'm sorry, I wasn't able to process that. Could you try rephrasing?"
                st.markdown(fallback)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": fallback,
                    "agent": "Router",
                })
