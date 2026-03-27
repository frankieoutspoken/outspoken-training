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
