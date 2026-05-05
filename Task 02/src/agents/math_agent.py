from openai import Agent
from tools.math_tool import calculate_math

math_agent = Agent(
    name="MathAgent",
    instructions="""
    You solve math problems.
    Convert word problems into expressions before calling the tool.
    """,
    tools=[calculate_math]
)