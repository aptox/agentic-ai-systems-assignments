import requests
from agents import function_tool


@function_tool
def get_weather(city: str) -> str:
    """
    Retrieve the current temperature for a given city.

    Uses the Open-Meteo geocoding API to resolve the city name to coordinates,
    then queries the Open-Meteo weather API for the current temperature.

    Args:
        city (str): The name of the city to get the weather for.
                    Examples: "Haifa", "New York City", "Tokyo", "London".

    Returns:
        str: The current temperature in Celsius, formatted as "{temp}°C".

    Raises:
        ValueError: If the city name cannot be resolved to coordinates.
        requests.exceptions.HTTPError: If the API request returns an unsuccessful status code.
        requests.exceptions.RequestException: For underlying network or connection issues.

    Example:
        >>> get_weather("Haifa")
        '24.1°C'
    """
    with requests.Session() as session:
        # Step 1: Geocode the city name to lat/lon
        geo_response = session.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=30
        )
        geo_response.raise_for_status()
        geo_data = geo_response.json()

        if not geo_data.get("results"):
            raise ValueError(f"Could not find coordinates for city: '{city}'")

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]

        # Step 2: Fetch current temperature from weather API
        weather_response = session.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current": "temperature_2m"},
            timeout=10
        )
        weather_response.raise_for_status()
        weather_data = weather_response.json()

    temp = float(weather_data["current"]["temperature_2m"])
    return f"{temp}°C"
