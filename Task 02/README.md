# AI Systems Architecture and Engineering Course

## Homework Assignment 2

### Optimization and Prompt Engineering with OpenAI Agents SDK

---

## 🎯 Objective of the Assignment

* In Assignment 1, you implemented a smart bot with routing, memory, and conversation management.
* In this assignment, you will upgrade the system’s **“brain”**, focusing on:

  * Improving decision quality
  * Increasing classification reliability
  * Extracting structured information
  * Managing responsibilities between agents
  * Adding defense mechanisms
* The assignment **must be implemented using the OpenAI Agents SDK**, not as a regular chatbot.

### Required Capabilities

Your solution must explicitly include:

* Agents
* Tools
* Handoffs
* Input Guardrails
* Output Guardrails

### Goal

Build a **modular, reliable, and secure multi-agent system**, extending your previous bot into a full Agents-based architecture.

---

## 🏗️ General Architecture

Your system must include multiple agents with clearly defined roles:

### Router Agent

* Analyzes user input
* Determines intent
* Decides how to handle the request

### Task Agents

Dedicated agents for specific tasks, such as:

* Weather Agent
* Calculations Agent
* Exchange Rates Agent
* General Chat Agent

### Handoffs

* Agents must transfer control using **handoffs**, not manual logic
* The Router decides which agent should handle the request

### Tools

* System capabilities must be implemented as **deterministic tools**
* Agents call tools when needed

### Guardrails

* Input Guardrails: validate safety and correctness before processing
* Output Guardrails: validate responses before returning them

---

## 🧩 Part A: Router Upgrade (Zero-Shot → Few-Shot)

### Requirements

* Build a **Router Agent** that classifies input into one of:

  ```
  getWeather
  calculateMath
  getExchangeRate
  generalChat
  ```

* Use **Few-Shot Prompting**:

  * At least **3 examples per category**
  * Include **edge cases and ambiguous inputs**

### Example

Input:

> "I am flying to London and need to know if I should take a coat"

Correct classification:

```
getWeather
```

⚠️ Must be implemented as a **dedicated agent**, not a simple model call.

---

## 🧾 Part B: Structured Output

### Required Output Format

The Router must return a structured object:

```json
{
  "intent": "getWeather",
  "parameters": {
    "city": "London"
  },
  "confidence": 0.93
}
```

### Requirements

* Include:

  * `intent`
  * `parameters`
  * `confidence` (0–1)
* Use SDK-native structured output (not string parsing)
* Validate structure before use

---

## 🧮 Part C: Solving Word Problems

### Goal

Handle **natural language math problems**

### Example

> "Yossi has 5 apples, he ate 2 and bought 10 more. How many does he have?"

### Requirements

Your system must:

1. Analyze the problem
2. Convert it into a mathematical expression
3. Send it to a deterministic calculation tool

⚠️ Important:

* The LLM **must not perform calculations**
* It only translates language → math

---

## 🛠️ Part D: Required Tools

Implement at least:

### `getWeather`

* Input: city
* Output: real-time weather
* Must use an external API

### `calculateMath`

* Input: mathematical expression
* Output: exact result (deterministic code)

### `getExchangeRate`

* Returns currency exchange rates
* Can be static or API-based

### `generalChat`

* Handles open conversation
* Implemented via a dedicated agent

---

## 🔁 Part E: Handoffs Between Agents

### Requirements

* Requests must flow between agents using **handoffs**

### Example Flow

1. Router detects weather request
2. Handoff to Weather Agent
3. Weather Agent calls tool
4. Output Guardrail validates result
5. Response returned

✅ Must demonstrate at least **2 real handoffs**

---

## 🛡️ Part F: Input Guardrails

Implement at least **2 protections**, such as:

* Invalid or empty input detection
* Unsupported request detection
* Malicious code detection
* Political content detection
* Parameter validation (e.g., city, currency)

### Behavior

* Invalid input must be:

  * Blocked, or
  * Safely redirected

---

## 🚨 Part G: Output Guardrails

Implement at least **2 protections**, such as:

* Valid JSON structure enforcement
* Content safety filtering
* Format validation
* Policy compliance checks

### Requirement

* Demonstrate at least **one case where an output is blocked or corrected**

---

## 🎭 Part H: Persona & Boundaries

### General Chat Agent Personality

* Cynical but helpful research assistant
* Short responses
* Occasionally uses **data engineering metaphors**
* Consistent tone

### Safety Rules

Must refuse:

* Political questions
* Malicious code requests
* Other unsafe content

### Required Response

```
"I cannot process this request due to safety protocols."
```

---

## 🧠 Part I: Memory & Context

### Requirements

* Load conversation history from file on startup
* Save history after each interaction
* Support a `reset` command
* Inject context into `generalChat` when needed

---

## 📦 Submission Deliverables

### 1. Full Code

* All project files

### 2. Prompts File

* All agent prompts and instructions

### 3. Execution Logs / Screenshots

Must include:

* Complex input classification (Few-Shot)
* Router structured output
* Word problem → expression → solution
* Real agent handoff
* Input Guardrail blocking
* Output Guardrail validation/block
* Persona-based response
* Safety refusal example
* Memory persistence demonstration

### 4. Explanatory Document (1–2 pages)

Include:

* Architecture overview
* Agents and roles
* Tools used
* Handoff logic
* Guardrails design
* Memory management explanation

---

## 🏆 Evaluation Criteria

* Functional correctness
* Proper use of OpenAI Agents SDK
* Clear separation between Agents and Tools
* Correct implementation of Handoffs
* Prompt engineering quality
* Structured output correctness
* Safety mechanisms quality
* Code organization and clarity
* Quality of execution examples
