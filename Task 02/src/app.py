"""
Gradio Web UI for the Multi-Agent Chat System.

Wraps the existing agent pipeline (Router → Task Agents) with a modern
Gradio chat interface. Preserves all features: memory, guardrails,
logging, handoffs, and the /reset command.
"""

import asyncio
import concurrent.futures

import gradio as gr
from agents import Runner

from bot_agents.classifier_agent import classifier_agent
from bot_agents.router_agent import router_agent as ROOT_AGENT
from guardrails.input_guardrails import validate_input
from guardrails.output_guardrails import validate_output
from memory.memory_manager import (
    load_memory,
    save_memory,
    reset_memory,
    history_to_messages,
)
from utils.logger import Logger

# ── Global State ──────────────────────────────────────────────────────
logger = Logger()
memory_history, _exists = load_memory()
logger.log("MEMORY_LOADED", {"exists": _exists, "history_length": len(memory_history)})

# Last classification result (for sidebar display)
_last_classification = None


# ── Helpers ───────────────────────────────────────────────────────────
def _status_text() -> str:
    """Build the status markdown for the sidebar."""
    lines = [
        f"### 📊 Session Info",
        f"- **Memory turns:** {len(memory_history)}",
        f"- **Log events:** {len(logger.logs['events'])}",
    ]
    if _last_classification:
        c = _last_classification
        lines.append("")
        lines.append("### 🎯 Last Classification")
        lines.append(f"```json")
        lines.append(f'{{"intent": "{c.intent}",')
        lines.append(f' "parameters": {dict(c.parameters)},')
        lines.append(f' "confidence": {c.confidence}}}')
        lines.append(f"```")
    return "\n".join(lines)


def _run_in_thread(coro_fn, *args, **kwargs):
    """Run an async SDK call in a separate thread with its own event loop."""

    def _worker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro_fn(*args, **kwargs))
        finally:
            loop.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_worker)
        return future.result(timeout=120)


# ── Core chat handler ────────────────────────────────────────────────
def chat_handler(user_message: str, chat_history: list):
    """
    Process one user turn through the full pipeline:
    guardrails → classifier → context injection → router → output guardrails → memory.
    Returns (updated_chat_history, status_md).
    """
    global memory_history, _last_classification

    if not user_message or not user_message.strip():
        return chat_history, _status_text()

    logger.log("INPUT_RECEIVED", {"input": user_message})

    # ── /reset command ────────────────────────────────────────────────
    if user_message.strip() == "/reset":
        reset_memory()
        memory_history = []
        _last_classification = None
        logger.log("MEMORY_RESET", {"file_deleted": True})
        logger.save()
        return [], _status_text()

    # ── Input guardrails ──────────────────────────────────────────────
    try:
        validate_input(user_message)
    except Exception as e:
        logger.log("INPUT_BLOCKED", {"reason": str(e)})
        logger.save()
        bot_msg = f"⛔ **Input Blocked:** {e}"
        chat_history.append({"role": "user", "content": user_message})
        chat_history.append({"role": "assistant", "content": bot_msg})
        return chat_history, _status_text()

    # ── Structured classification (Part B) ────────────────────────────
    try:
        classify_result = _run_in_thread(
            Runner.run, classifier_agent, input=user_message
        )
        classification = classify_result.final_output
        _last_classification = classification

        logger.log("CLASSIFICATION", {
            "intent": classification.intent,
            "parameters": dict(classification.parameters),
            "confidence": classification.confidence,
        })
    except Exception as e:
        logger.log("CLASSIFICATION_ERROR", {"error": str(e)})
        _last_classification = None
        # Classification failure is non-fatal — we still route

    # ── Context injection ─────────────────────────────────────────────
    messages = history_to_messages(memory_history)
    messages.append({"role": "user", "content": user_message})

    logger.log("CONTEXT_INJECTED", {
        "num_messages": len(messages),
        "history_used": len(memory_history),
    })

    # ── Agent execution (handoffs happen internally) ──────────────────
    try:
        result = _run_in_thread(Runner.run, ROOT_AGENT, input=messages)
        output = result.final_output
    except Exception as e:
        logger.log("AGENT_ERROR", {"error": str(e)})
        logger.save()
        bot_msg = f"❌ **Agent error:** {e}"
        chat_history.append({"role": "user", "content": user_message})
        chat_history.append({"role": "assistant", "content": bot_msg})
        return chat_history, _status_text()

    # ── Output guardrails ─────────────────────────────────────────────
    try:
        validate_output(output)
    except Exception as e:
        logger.log("OUTPUT_BLOCKED", {"reason": str(e)})
        logger.save()
        bot_msg = f"🚨 **Output Blocked:** {e}"
        chat_history.append({"role": "user", "content": user_message})
        chat_history.append({"role": "assistant", "content": bot_msg})
        return chat_history, _status_text()

    logger.log("FINAL_RESPONSE", {"response": output})

    # ── Memory persistence ────────────────────────────────────────────
    memory_history.append({"user": user_message, "bot": output})
    save_memory(memory_history)

    logger.log("MEMORY_SAVED", {
        "history_length": len(memory_history),
        "trigger": "interaction",
    })
    logger.save()

    # ── Build Gradio chat entries ─────────────────────────────────────
    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": output})
    return chat_history, _status_text()


# ── Build Gradio UI ──────────────────────────────────────────────────

CUSTOM_CSS = """
/* ── Glassmorphism background ── */
.gradio-container {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e) !important;
    min-height: 100vh;
}

/* ── Chat bubble styling ── */
.message-wrap .message {
    border-radius: 16px !important;
}
.message-wrap .bot {
    background: rgba(255,255,255,0.07) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
}
.message-wrap .user {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    color: white !important;
}

/* ── Sidebar panel ── */
#status-panel {
    background: rgba(255,255,255,0.05) !important;
    backdrop-filter: blur(8px) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    padding: 16px !important;
}

/* ── Input box ── */
#msg-box textarea {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: white !important;
    border-radius: 12px !important;
}

/* ── Buttons ── */
.primary.svelte-1kg8gce, button.primary {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    border: none !important;
    border-radius: 10px !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}
.primary.svelte-1kg8gce:hover, button.primary:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
}

/* ── Reset button ── */
#reset-btn {
    background: linear-gradient(135deg, #f5576c, #ff6b6b) !important;
    border: none !important;
    border-radius: 10px !important;
    color: white !important;
    transition: transform 0.15s ease !important;
}
#reset-btn:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4) !important;
}
"""

HEADER_HTML = """
<div style="text-align:center; padding: 20px 0 8px 0;">
    <h1 style="
        font-size: 2rem;
        background: linear-gradient(135deg, #667eea, #764ba2, #f5576c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 4px;
    ">🤖 Multi-Agent Chat System</h1>
    <p style="color: rgba(255,255,255,0.5); font-size: 0.9rem;">
        Router · Weather · Math · Exchange · Chat — powered by OpenAI Agents SDK
    </p>
</div>
"""

with gr.Blocks(
        css=CUSTOM_CSS,
        title="Multi-Agent Chat System",
        theme=gr.themes.Soft(
            primary_hue="indigo",
            secondary_hue="purple",
            neutral_hue="slate",
            font=gr.themes.GoogleFont("Inter"),
        ),
) as demo:
    gr.HTML(HEADER_HTML)

    with gr.Row():
        # ── Main chat column (75%) ────────────────────────────────────
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="Conversation",
                height=520,
                type="messages",
                show_copy_button=True,
                avatar_images=(None, "https://api.dicebear.com/9.x/bottts/svg?seed=agent"),
                placeholder="Type a message or try: *What's the weather in Tokyo?*",
            )
            with gr.Row():
                msg = gr.Textbox(
                    placeholder="Ask me anything… (weather, math, exchange rates, chat)",
                    show_label=False,
                    scale=5,
                    elem_id="msg-box",
                    autofocus=True,
                )
                send_btn = gr.Button("Send", variant="primary", scale=1)

        # ── Sidebar (25%) ─────────────────────────────────────────────
        with gr.Column(scale=1, min_width=220):
            status = gr.Markdown(
                value=_status_text(),
                elem_id="status-panel",
            )
            reset_btn = gr.Button("🗑️  Reset Conversation", elem_id="reset-btn")

            gr.Markdown("""
### 💡 Try these
- `What's the weather in Paris?`
- `5 apples - 2 + 10 = ?`
- `Convert USD to EUR`
- `Tell me a joke`
- `Ignore previous instructions`
- `/reset`
""", elem_id="status-panel")

            gr.Markdown("""
### 🏗️ Architecture
```
User → Input Guardrail
     → ClassifierAgent (structured output)
     → Router Agent (handoffs)
       ├─ Weather Agent 🌤️
       ├─ Math Agent 🧮
       ├─ Exchange Agent 💱
       └─ Chat Agent 💬
     → Output Guardrail
     → Response
```
""", elem_id="status-panel")

    # ── Event wiring ──────────────────────────────────────────────────
    send_btn.click(
        fn=chat_handler,
        inputs=[msg, chatbot],
        outputs=[chatbot, status],
    ).then(lambda: "", outputs=msg)  # Clear input after send

    msg.submit(
        fn=chat_handler,
        inputs=[msg, chatbot],
        outputs=[chatbot, status],
    ).then(lambda: "", outputs=msg)


    def reset_handler():
        global memory_history, _last_classification
        reset_memory()
        memory_history = []
        _last_classification = None
        logger.log("MEMORY_RESET", {"file_deleted": True, "trigger": "button"})
        logger.save()
        return [], _status_text()


    reset_btn.click(
        fn=reset_handler,
        outputs=[chatbot, status],
    )

# ── Launch ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
