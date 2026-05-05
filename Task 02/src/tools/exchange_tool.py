from openai import tool
import requests

@tool
def get_exchange_rate(frm: str, to: str) -> float:
    """
    Get the current exchange rate from one currency to another.
    Uses the free ExchangeRate-API (no API key required) to fetch
    real-time exchange rates.

    Args:
        frm (str): The source currency code (e.g. "USD", "EUR", "ILS").
        to  (str): The target currency code (e.g. "USD", "EUR", "ILS").

    Returns:
        float: The exchange rate representing how many units of `to`
               equal one unit of `frm`.

    Raises:
        ValueError: If either currency code is not supported by the API.
        requests.exceptions.HTTPError: If the API returns an error status.
        requests.exceptions.RequestException: For network/connection issues.

    Example:
        >>> rate = get_exchange_rate("USD", "ILS")
        >>> print(f"1 USD = {rate} ILS")
        1 USD = 3.62 ILS
    """
    frm = frm.upper().strip()
    to = to.upper().strip()

    response = requests.get(
        f"https://open.er-api.com/v6/latest/{frm}",
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("result") != "success":
        raise ValueError(f"API error: {data.get('error-type', 'unknown error')}")

    rates = data.get("rates", {})
    if to not in rates:
        raise ValueError(f"Unsupported target currency: '{to}'")

    return float(rates[to])
