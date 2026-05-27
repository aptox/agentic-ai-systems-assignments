# Task 03 — Explanatory Document
## Review Summarizer & Insight Extraction

---

## 1. System Structure

The system is a multi-agent pipeline built with the **OpenAI Agents SDK**, exposed via a **Gradio** web interface. Every user message travels through five sequential stages before a response is shown.

```
User Input
    │
    ▼
┌─────────────────────┐
│   Input Guardrails  │  Rule checks + LLM safety classifier
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  ClassifierAgent    │  Structured output → RouteOutput (intent + params + confidence)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    RouterAgent      │  Reads intent → SDK handoff to specialist agent
└──────────┬──────────┘
           │
     ┌─────┴──────────────────────────────────────┐
     │                                            │
     ▼                                            ▼
WeatherAgent / MathAgent /              ReviewAnalyzerAgent
ExchangeAgent / ChatAgent                    │
                                             ▼
                                    Self-Correction Layer
                                    (sanity check → optional 2nd LLM call)
     │                                            │
     └─────────────────────┬──────────────────────┘
                           ▼
              ┌────────────────────────┐
              │   Output Guardrails    │  Rule checks + LLM safety classifier
              └────────────┬───────────┘
                           ▼
                    Formatted Response
                    (Gradio chat UI)
```

### Key files

| File | Role |
|---|---|
| `src/app.py` | Gradio UI, chat handler, review post-processing |
| `src/bot_agents/classifier_agent.py` | ClassifierAgent definition |
| `src/bot_agents/router_agent.py` | RouterAgent + handoff wiring |
| `src/bot_agents/review_analyzer_agent.py` | ReviewAnalyzerAgent definition |
| `src/bot_agents/self_correction.py` | `sanity_check()` + `correct_review_async()` |
| `src/bot_agents/schemas.py` | Pydantic models: `RouteOutput`, `ReviewAspect`, `ReviewOutput` |
| `src/prompts/classifier_prompt.txt` | Few-shot classifier instructions |
| `src/prompts/router_prompt.txt` | Router routing instructions |
| `src/prompts/review_analyzer_prompt.txt` | ABSA + slang/sarcasm prompt |
| `src/guardrails/input_guardrails.py` | Input validation (rules + LLM) |
| `src/guardrails/output_guardrails.py` | Output validation (rules + LLM) |
| `src/memory/memory_manager.py` | JSON-file conversation memory |
| `src/utils/logger.py` | Session event logger |

---

## 2. How the Router Works

Routing happens in two sequential steps: **classification** then **handoff**.

### Step 1 — ClassifierAgent (Structured Output)

Before routing, a dedicated `ClassifierAgent` runs first. It uses SDK-native structured output (`output_type=AgentOutputSchema(RouteOutput)`) to force the model to return a validated Pydantic object with three fields:

```python
class RouteOutput(BaseModel):
    intent: str        # one of: getWeather, calculateMath, getExchangeRate,
                       #          analyzeReview, generalChat
    parameters: dict   # extracted params (city, expression, reviewText, etc.)
    confidence: float  # 0.0 – 1.0
```

The classifier prompt uses few-shot examples to teach the model to recognise free-form Hebrew reviews as `analyzeReview` and extract the full `reviewText` parameter from them. Classification is non-fatal — if it errors the system still routes via the RouterAgent.

### Step 2 — RouterAgent (SDK Handoffs)

The `RouterAgent` receives the full conversation context and uses the OpenAI Agents SDK `handoff()` mechanism to delegate to the correct specialist:

| Intent | Target Agent |
|---|---|
| `getWeather` | `WeatherAgent` — calls `get_weather(city)` tool |
| `calculateMath` | `MathAgent` — calls `calculate_math(expression)` tool |
| `getExchangeRate` | `ExchangeAgent` — calls `get_exchange_rate(frm, to)` tool |
| `analyzeReview` | `ReviewAnalyzerAgent` — returns structured JSON |
| `generalChat` | `ChatAgent` — free conversation |

The router prompt includes five few-shot examples specifically for `analyzeReview`, covering plain Hebrew, Hebrew with slang, sarcastic phrasing, explicit "analyze this review" requests, and English reviews. The router identifies review intent purely from the natural language — no special prefix is required from the user.

---

## 3. How Review Analysis Is Performed

When the router hands off to `ReviewAnalyzerAgent`, the agent receives the full conversation context (including the review text) and is governed by `review_analyzer_prompt.txt`.

### What the prompt instructs the model to do

1. **Return only valid JSON** — no markdown fences, no surrounding text, nothing outside the JSON object.
2. **Extract aspects** — identify only topics actually mentioned in the review (Food, Service, Price, Atmosphere, Cleanliness, Delivery, Product Quality, Wait Time, etc.). Inventing aspects not in the text is explicitly forbidden.
3. **Assign per-aspect sentiment** — each aspect gets its own `Positive`, `Negative`, or `Neutral` label independently from the others.
4. **Compute an overall sentiment** — `Positive`, `Negative`, `Neutral`, or `Mixed`.
5. **Score from 1–10** — consistent with the overall sentiment label (see self-correction below).
6. **Write a one-sentence English summary** regardless of the input language.

### JSON output schema

```json
{
  "summary": "One concise sentence summarising the review.",
  "overall_sentiment": "Positive | Negative | Neutral | Mixed",
  "score": 6,
  "aspects": [
    { "topic": "Food",    "sentiment": "Positive", "detail": "quote or paraphrase" },
    { "topic": "Price",   "sentiment": "Negative", "detail": "quote or paraphrase" },
    { "topic": "Service", "sentiment": "Negative", "detail": "quote or paraphrase" }
  ]
}
```

### Why JSON mode

Using JSON-only output prevents hallucinated prose and guarantees a machine-readable structure that can be:
- validated with the `ReviewOutput` Pydantic model,
- fed directly into the sanity-check function,
- formatted deterministically into a readable markdown card for the user.

### Preventing hallucinations

- The prompt explicitly forbids inventing aspects not present in the text.
- Four diverse few-shot examples anchor the model's output format.
- The Pydantic `ReviewOutput` model validates the JSON before it is shown; if the model returns malformed JSON, the raw string falls through gracefully.
- The self-correction layer catches score/sentiment mismatches that indicate the model lost coherence mid-response.

### Display formatting

In `app.py`, the raw JSON is detected (starts with `{`, contains `overall_sentiment` and `aspects`), passed through the self-correction pipeline, then rendered as a human-readable markdown card:

```
📋 Review Analysis

Summary: Exceptional burger but the experience was hurt by high prices and dismissive service.
Overall Sentiment: 🟠 Mixed
Score: 6/10

Aspects:
1. Food (🟢 Positive): "המבורגר כזה עוד לא אכלתי, פשוט וואו"
2. Price (🔴 Negative): "המחיר? שחיטה"
3. Service (🔴 Negative): "מארחת שגלגלה עיניים" (sarcasm/attitude detected)
```

---

## 4. How Slang and Sarcasm Are Handled

Real-world reviews — especially in Hebrew — contain expressions where the surface meaning and the intended sentiment are opposite or context-dependent. Handling these correctly is done entirely at the **prompt level**, inside `review_analyzer_prompt.txt`.

### Positive slang → POSITIVE sentiment

| Expression | Meaning |
|---|---|
| `"אש"` / `"אחלה"` / `"סבבה"` | Great, excellent |
| `"וואו"` | Very impressed |
| `"חבל על הזמן"` *about food or quality* | So good it's almost a shame — POSITIVE |
| `"הצגה"` *about food* | A show-stopper, outstanding |
| `"המבורגר כזה עוד לא אכלתי"` | Never had such a good burger — POSITIVE |

### Negative slang → NEGATIVE sentiment

| Expression | Meaning |
|---|---|
| `"שחיטה"` *about price* | Rip-off, outrageously expensive |
| `"דפק איחור"` / `"דפק אותנו"` | Screwed up, caused a problem |
| `"חסר סבלנות"` | Impatient, rude |
| `"חבל על הזמן"` *about wait or service* | Waste of time — NEGATIVE |
| `"ממש זול"` *about product feel* | Cheap quality — NEGATIVE |
| `"לא ממש עזר"` | Wasn't helpful — NEGATIVE |

### Context sensitivity

The same phrase can carry **opposite** sentiment depending on what it refers to:

- `"חבל על הזמן"` + food → **POSITIVE** ("so good")
- `"חבל על הזמן"` + wait time → **NEGATIVE** ("waste of time")

The prompt instructs the model to resolve this by examining the surrounding context before assigning sentiment.

### Sarcasm detection

Sarcasm is identified when tone contradicts literal meaning. The prompt provides explicit sarcasm markers:

- `"איזה כיף"` followed by a complaint → **sarcastic, NEGATIVE**
  - *Example: "איזה כיף, שוב חיכינו ארבעים דקות למנה" → Negative, score 2/10*
- `"ממש תודה ל..."` followed by a rude action → **sarcastic, NEGATIVE**
  - *Example: "ממש תודה למארחת שגלגלה עיניים" → Negative service*
- When sarcasm is detected, the surface sentiment is **inverted**.

Four few-shot examples in the prompt demonstrate exactly how these cases should be handled, giving the model concrete input/output pairs to match against.

---

## 5. The Self-Correction Mechanism

### Why it exists

A language model can produce internally inconsistent output — for example, labelling the overall sentiment as `"Positive"` but assigning a `score` of `2`. This indicates the model lost coherence between the two fields. The self-correction layer catches these contradictions **before** the response is shown to the user.

### Stage 1 — Sanity Check (`sanity_check()` in `self_correction.py`)

After `ReviewAnalyzerAgent` returns its JSON, `sanity_check()` applies two deterministic rules:

**Rule 1 — Score/sentiment consistency**

Each sentiment label has an expected score range:

| Sentiment | Expected score range |
|---|---|
| Positive | 7 – 10 |
| Neutral | 4 – 6 |
| Negative | 1 – 4 |
| Mixed | 3 – 8 |

If the score falls outside the expected range for the given sentiment label, a contradiction is reported.

**Rule 2 — Aspect/sentiment consistency**

If `overall_sentiment` is `"Positive"` but the majority of extracted aspects are Negative (more negatives than positives), or vice-versa, a contradiction is reported.

If no contradiction is found, `sanity_check()` returns `None` and the output is used as-is.

### Stage 2 — Correction (`correct_review_async()`)

If a contradiction is detected, a **second LLM call** is made using a lightweight `CorrectionAgent`. The prompt sent to it contains:

1. The original review text
2. The inconsistent JSON
3. A precise description of the detected contradiction

Example correction prompt:
```
Original review:
<the user's review text>

Current JSON output (contains a contradiction):
<the inconsistent JSON>

Contradiction detected: overall_sentiment is 'Positive' but score is 2.
Expected score in range 7–10 for Positive sentiment.

Please fix this inconsistency. Return corrected JSON only.
```

The `CorrectionAgent` returns a corrected JSON object. The result is parsed and validated — if the correction itself is invalid JSON or identical to the original, the system falls back to the original output. A correction note is added to the displayed card when a fix was applied:

> ✏️ *Self-correction applied — output was inconsistent and was automatically fixed.*

### Full flow

```
ReviewAnalyzerAgent returns JSON
        │
        ▼
   sanity_check()
        │
   ┌────┴─────────────────────────────────────────────┐
   │ No contradiction                                 │ Contradiction found
   ▼                                                  ▼
Use output as-is                          correct_review_async()
                                                   │
                                         ┌─────────┴──────────────┐
                                         │ Correction valid        │ Correction failed
                                         ▼                         ▼
                                  Use corrected JSON         Use original JSON
                                  + show ✏️ note
        │
        ▼
_format_review_output() → Markdown card → User
```

---

## 6. Design Decisions

**JSON mode for review analysis** — Returning structured JSON instead of prose makes the output deterministic, machine-parseable, and independently validatable. It also makes the self-correction check possible with simple rules rather than requiring another LLM call to interpret free text.

**Three-stage pipeline (Classifier → Router → Specialist)** — The ClassifierAgent adds a structured pre-classification step that makes intent and parameters explicit before routing. This improves debuggability (the sidebar shows intent, parameters, and confidence for every turn) and allows the router to operate on cleaner signal.

**Prompt-level slang/sarcasm handling** — Handling nuance in the system prompt (rather than in code) means no external sentiment library or NLP model is needed. The prompt's explicit slang glossary and sarcasm markers are easy to extend and work across both Hebrew and English inputs.

**Graceful self-correction fallback** — If the correction LLM call fails for any reason (network error, invalid JSON returned, etc.), the original output is used unchanged. The correction is always a best-effort improvement, never a hard dependency.

**Non-fatal classification** — If `ClassifierAgent` errors, the system logs it and continues directly to `RouterAgent`. The router can still route correctly from the raw message text; the classification step is an enhancement, not a gate.
