# Task 02 — Explanatory Document

## Architecture Overview

The system is built as a **modular multi-agent pipeline** using the **OpenAI Agents SDK**. Every user message flows through a structured pipeline:

```
User Input
  → Input Guardrails (rule-based + LLM safety classifier)
  → ClassifierAgent (SDK-native structured output → {intent, parameters, confidence})
  → RouterAgent (handoffs to task agents)
    ├─ WeatherAgent → get_weather tool (Open-Meteo API)
    ├─ MathAgent → calculate_math tool (AST-based evaluator)
    ├─ ExchangeAgent → get_exchange_rate tool (ExchangeRate API)
    └─ ChatAgent (persona-driven general conversation)
  → Output Guardrails (rule-based + LLM safety classifier)
  → Response
```

The UI is a **Gradio web interface** (`app.py`) with a dark glassmorphism theme. A CLI entry point (`main.py`) is also available.

---

## Agents and Roles

| Agent | Role | SDK Feature |
|---|---|---|
| **ClassifierAgent** | Classifies user intent into structured JSON (`{intent, parameters, confidence}`) | `output_type=RouteOutput` (Pydantic model via `AgentOutputSchema`) |
| **RouterAgent** | Receives user input and delegates to the appropriate task agent | `handoffs=[WeatherAgent, MathAgent, ExchangeAgent, ChatAgent]` |
| **WeatherAgent** | Fetches real-time weather for a given city | `tools=[get_weather]` |
| **MathAgent** | Translates word problems into expressions and uses the deterministic math tool. The LLM never calculates — it only translates. | `tools=[calculate_math]` |
| **ExchangeAgent** | Fetches live currency exchange rates | `tools=[get_exchange_rate]` |
| **ChatAgent** | Handles general conversation with a cynical research assistant persona | Persona prompt loaded from `chat_prompt.txt` |

---

## Tools Used

All tools are implemented as **deterministic functions** decorated with `@function_tool` from the Agents SDK. The LLM never performs computations directly — it calls tools.

| Tool | Input | Output | Implementation |
|---|---|---|---|
| `get_weather(city)` | City name (str) | Temperature as `"{temp}°C"` (str) | Open-Meteo Geocoding + Weather API |
| `calculate_math(expression)` | Math expression (str) | Numeric result as string | Python AST parser — safe alternative to `eval()` |
| `get_exchange_rate(frm, to)` | Two currency codes (str) | Exchange rate as string | ExchangeRate API (open.er-api.com) |

---

## Handoff Logic

The **RouterAgent** uses SDK-native `handoff()` declarations. When it receives user input, it analyzes the message and selects the most appropriate agent via the SDK's built-in handoff mechanism. This is NOT manual routing — the SDK's Agent runtime manages the control transfer.

```python
router_agent = Agent(
    name="RouterAgent",
    instructions=router_prompt,  # Few-shot prompt with ≥3 examples/category
    handoffs=[
        handoff(weather_agent),
        handoff(math_agent),
        handoff(exchange_agent),
        handoff(chat_agent),
    ]
)
```

The router prompt uses **Few-Shot Prompting** with examples for each category, including edge cases like indirect weather queries ("Should I take a coat to London?").

---

## Guardrails Design

### Input Guardrails (3 protections)

1. **Empty/Length Check**: Rejects empty input or messages exceeding 500 characters.
2. **Pattern-Based Injection Detection**: Regex patterns catch common prompt injection attempts (e.g., "ignore previous instructions", "system prompt").
3. **LLM Safety Classifier**: An OpenAI `gpt-4o-mini` call classifies input as SAFE or MALICIOUS/POLITICAL. Uses `temperature=0` for deterministic classification.

### Output Guardrails (3 protections)

1. **Null Check**: Blocks empty/None responses.
2. **Length Check**: Blocks responses exceeding 1000 characters.
3. **LLM Safety Classifier**: Same `gpt-4o-mini` model validates the output for safety before returning to the user.

---

## Structured Output

The **ClassifierAgent** uses the SDK's native `output_type` parameter with a **Pydantic model** (`RouteOutput`):

```python
class RouteOutput(BaseModel):
    intent: str       # getWeather | calculateMath | getExchangeRate | generalChat
    parameters: dict   # e.g. {"city": "Tokyo"} or {"expression": "5-2+10"}
    confidence: float  # 0.0 to 1.0
```

This runs before the RouterAgent and produces validated, structured JSON that is:
- **Logged** to `logs/latest.json` for every interaction
- **Displayed** in the Gradio sidebar under "Last Classification"
- **Validated** by Pydantic before use

---

## Memory Management

- **Persistence**: Conversation history is stored in `memory/history.json` as a JSON array of `{user, bot}` turn pairs.
- **Load on Startup**: History is loaded when the app starts, allowing conversation continuity.
- **Save After Each Turn**: After every successful interaction, the updated history is written to disk.
- **Reset**: The `/reset` command and the "Reset Conversation" button clear both the in-memory state and the `history.json` file.
- **Context Injection**: Previous turns are converted into OpenAI-format messages and prepended to the current request, giving the agent conversational memory.
