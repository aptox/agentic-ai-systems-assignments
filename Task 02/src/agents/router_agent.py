from openai import Agent, handoff
from agents.weather_agent import weather_agent
from agents.math_agent import math_agent
from agents.exchange_agent import exchange_agent
from agents.chat_agent import chat_agent

router_agent = Agent(
    name="RouterAgent",
    instructions=open("prompts/router_prompt.txt").read(),

    handoffs=[
        handoff(weather_agent),
        handoff(math_agent),
        handoff(exchange_agent),
        handoff(chat_agent),
    ]
)