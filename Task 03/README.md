# Task 03 — Review Summarizer & Insight Extraction

**Course:** Agentic AI Systems — Architecture and Engineering
**Assignment:** Home Assignment #3 — Sentiment Analysis & Text Summarization

---

## Overview

In Assignment 2, you built a bot capable of recognizing basic intents and performing simple actions (e.g., weather queries, calculations). This assignment upgrades that system to tackle one of the central challenges in modern AI systems: **processing unstructured text and converting it into structured, valuable insights**.

Instead of short, simple commands, the system now handles free-form user text — specifically, reviews of restaurants, hotels, services, or products — and is expected to:

- Understand what the user actually wrote
- Identify sentiments and opinions
- Break the review into distinct aspects
- Produce a concise summary
- Handle slang and sarcasm
- Perform a self-consistency check before presenting output

---

## What You Need to Implement

| Feature | Description |
|---|---|
| **Aspect-Based Sentiment Analysis (ABSA)** | Decompose the review into aspects (e.g., food, service, price) with per-aspect sentiment |
| **Summarization** | Generate a concise one-sentence summary (Extractive or Abstractive) |
| **Slang & Sarcasm Handling** | Handle natural, "dirty" language including Israeli slang, indirect phrasing, irony, and sarcasm |
| **Self-Correction / Refinement** | A simple self-check mechanism that detects internal contradictions in the output and corrects them before presenting to the user |

---

## Part A — Extending the Router: Recognizing Review Analysis Intent

Until now, your router recognized basic requests like weather or math. It must now also detect when a user is submitting a free-text review or requesting analysis of a usage/service experience.

### Task

1. Update `ROUTER_SYSTEM_PROMPT` from Assignment 2 to support a new intent: **`analyzeReview`**
2. Add `analyzeReview` as a new supported function in the function list
3. Add **Few-Shot examples** that teach the model to recognize free-form reviews
4. When the model detects a review, it must extract at minimum the parameter **`reviewText`** — the original text of the review

### Few-Shot Examples

| User Input (Hebrew) | Expected Intent |
|---|---|
| `הייתי אתמול במסעדה, האוכל היה סבבה אבל המלצר שפך עליי מרק` | `analyzeReview` |
| `המלון היה נקי מאוד, אבל חיכינו שעה בצ'ק-אין והצוות לא ממש עזר` | `analyzeReview` |
| `תנתח לי את הביקורת הבאה: הפיצה הייתה מעולה אבל המחיר מוגזם` | `analyzeReview` |

---

## Part B — Aspect-Based Sentiment Analysis (ABSA) in JSON Mode

Most models can classify a review as "positive" or "negative". The real engineering challenge is understanding **what specifically** was positive and **what specifically** was negative within the same review.

### Task

1. Create a new System Prompt named **`REVIEW_ANALYZER_PROMPT`**
2. When the router identifies `analyzeReview`, the bot sends the text to this prompt
3. The prompt **must return only a JSON object** in a fixed, well-defined structure

### Required JSON Output Structure

```json
{
  "summary": "One short sentence summarizing the review",
  "overall_sentiment": "Positive | Negative | Neutral | Mixed",
  "score": 7,
  "aspects": [
    {
      "topic": "Food",
      "sentiment": "Positive",
      "detail": "The steak was delicious"
    },
    {
      "topic": "Service",
      "sentiment": "Negative",
      "detail": "Waiter was rude"
    },
    {
      "topic": "Price",
      "sentiment": "Neutral",
      "detail": "Expensive but worth it"
    }
  ]
}
```

### Technical Requirements

- Output **must be valid JSON only** — no free text outside the JSON
- The model **must not invent aspects** that do not appear in the text
- Must support **Mixed** sentiment reviews
- `score` must be in the range **1–10**

---

## Part C — Slang & Sarcasm Handling (Nuance Handling)

Real-world reviews often include slang, abbreviations, context-dependent expressions, sarcasm, and indirect criticism. Basic models tend to fail on these cases.

### Task

Inside `REVIEW_ANALYZER_PROMPT`, add explicit instructions for interpreting **Israeli slang** and detecting **sarcasm**.

### Examples the Model Must Handle Correctly

| Input | Correct Interpretation |
|---|---|
| `"האוכל היה אש"` | **Positive** — food was fire (great) |
| `"שחיטה"` in the context of price | **Negative** — rip-off |
| `"השליח דפק איחור"` | **Negative** — the courier was very late |
| `"חבל על הזמן"` about food | **Positive** — so good it's a shame |
| `"חבל על הזמן"` about wait time | **Negative** — what a waste of time |

> **Note:** Context is critical — the same phrase can carry opposite sentiment depending on what it refers to.

---

## Part D — Self-Correction / Refinement

Sometimes the model returns output with internal contradictions — for example, `overall_sentiment = Positive` but `score = 2`. This indicates the model failed to maintain consistency.

### Task

Implement a simple **sanity-check step** before presenting the result to the user.

- If an internal contradiction is detected → make a **second LLM call** with a short correction prompt
- The second call receives:
  - The original review text
  - The previous (inconsistent) JSON
- It must return **corrected JSON only**

### Example Correction Prompt

```
You detected a Positive sentiment but gave a score of 2.
Please fix this inconsistency based on the review.
Return corrected JSON only.
```

---

## Full Input / Output Example

**User Input:**
```
תשמעו, המבורגר כזה עוד לא אכלתי, פשוט וואו! אבל המחיר? שחיטה.
וממש תודה למארחת שגלגלה עיניים כשביקשנו עוד מפיות.
```

**Expected Console Output:**
```
Analyzing Review...

Summary: Excellent food, but the experience was hurt by high prices and poor service attitude.
Overall Sentiment: Mixed
Score: 6/10

Detailed Aspects:
1. Food (Positive): "המבורגר כזה עוד לא אכלתי, פשוט וואו"
2. Price (Negative): "המחיר? שחיטה"
3. Service (Negative): "מארחת שגלגלה עיניים" (sarcasm/attitude detected)
```

---

## Additional Run Examples

| Case | Input |
|---|---|
| **Hotel** | `החדר היה ענק ונקי, אבל המזגן לא עבד והפקיד בקבלה היה חסר סבלנות.` |
| **Pizza with slang** | `הפיצה הייתה הצגה, אבל השליח דפק איחור והכל כבר התקרר.` |
| **Product** | `החבילה הגיעה מהר והקופסה הייתה נראית טוב, אבל המוצר עצמו מרגיש ממש זול.` |
| **Sarcasm** | `איזה כיף, שוב חיכינו ארבעים דקות למנה.` |
| **Mostly positive** | `שירות מהיר, אוכל טעים, מחיר קצת גבוה אבל סך הכל חוויה מעולה.` |

---

## Recommended Architecture

Split the system into **3 stages**. This separation improves code readability, testability, debugging, and architectural explanation in the submission:

```
User Input
    │
    ▼
┌─────────┐
│ Router  │  Identifies intent → analyzeReview
└────┬────┘
     │
     ▼
┌──────────────────┐
│ Review Analyzer  │  REVIEW_ANALYZER_PROMPT → returns raw JSON
└────────┬─────────┘
         │
         ▼
┌──────────────────────┐
│ Self-Correction Layer│  Sanity check → second LLM call if inconsistent
└──────────────────────┘
         │
         ▼
    Structured Output
```

In your submission, explain:
- Why you used **JSON mode**
- How you tried to prevent **hallucinations**
- How you handled **slang and sarcasm**

---

## Deliverables

Submit all of the following in an organized, clear, and readable format:

### 1. Project Files
All code files required to run the solution:
- Source files
- Prompt files
- Main entry point
- Dependency file if applicable (`requirements.txt` or `package.json`)

The code must be **readable, modular, minimally documented, and runnable**.

### 2. Short Explanation File (README / Document)
A brief file explaining:
- System structure
- How the router works
- How review analysis is performed
- How slang and sarcasm are handled
- The self-correction mechanism

### 3. Log File / Run Examples
A log file with **at least 3 complete run examples**:

| # | Required Case |
|---|---|
| 1 | A normal review (restaurant, hotel, or product) |
| 2 | A complex review with Israeli slang or indirect phrasing |
| 3 | A demonstration of self-correction (if the model doesn't naturally produce a contradiction, an artificial example is allowed) |

### 4. Structured Output
Ensure that every `analyzeReview` run produces **valid JSON** and a **clear, explained output** in the console or interface.

---

Good luck!
