from openai import Agent
from tools.exchange_tool import get_exchange_rate

exchange_agent = Agent(
    name="ExchangeAgent",
    instructions="Handle currency conversions.",
    tools=[get_exchange_rate]
)