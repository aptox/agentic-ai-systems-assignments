from agents import Agent

from tools.weather_tool import get_weather

weather_agent = Agent(
    name="WeatherAgent",
    instructions="You handle weather requests. Extract city and call the tool.",
    tools=[get_weather]
)
