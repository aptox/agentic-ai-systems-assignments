from agents import Runner
from bot_agents.router_agent import router_agent as ROOT_AGENT
from bot_agents.classifier_agent import classifier_agent
from guardrails.input_guardrails import validate_input
from guardrails.output_guardrails import validate_output
from memory.memory_manager import (
    load_memory,
    save_memory,
    reset_memory,
    history_to_messages
)
from utils.logger import Logger
import atexit


def main():
    history, exists = load_memory()
    logger = Logger()

    # Log memory load
    logger.log("MEMORY_LOADED", {
        "exists": exists,
        "history_length": len(history)
    })

    if exists:
        print("Welcome back! Previous conversation loaded.")
    else:
        print("Starting a new conversation.")

    # Save on exit
    def on_exit():
        save_memory(history)
        logger.log("MEMORY_SAVED", {
            "history_length": len(history),
            "trigger": "exit"
        })
        logger.save()

    atexit.register(on_exit)

    while True:
        user_input = input("You: ")

        logger.log("INPUT_RECEIVED", {"input": user_input})

        # RESET
        if user_input == "/reset":
            reset_memory()
            history.clear()

            logger.log("MEMORY_RESET", {
                "file_deleted": True
            })

            print("Memory cleared.")
            continue

        # INPUT GUARDRAILS
        try:
            validate_input(user_input)
        except Exception as e:
            logger.log("INPUT_BLOCKED", {"reason": str(e)})
            print("Blocked:", e)
            continue

        # STRUCTURED CLASSIFICATION (Part B)
        try:
            classify_result = Runner.run_sync(classifier_agent, input=user_input)
            classification = classify_result.final_output
            logger.log("CLASSIFICATION", {
                "intent": classification.intent,
                "parameters": dict(classification.parameters),
                "confidence": classification.confidence,
            })
            print(f"  [Classification] intent={classification.intent}, "
                  f"params={dict(classification.parameters)}, "
                  f"confidence={classification.confidence}")
        except Exception as e:
            logger.log("CLASSIFICATION_ERROR", {"error": str(e)})

        # CONTEXT INJECTION
        messages = history_to_messages(history)
        messages.append({"role": "user", "content": user_input})

        logger.log("CONTEXT_INJECTED", {
            "num_messages": len(messages),
            "history_used": len(history)
        })

        result = Runner.run_sync(ROOT_AGENT, input=messages)

        output = result.final_output

        # OUTPUT GUARDRAILS
        try:
            validate_output(output)
        except Exception as e:
            logger.log("OUTPUT_BLOCKED", {"reason": str(e)})
            print("Output blocked:", e)
            continue

        print("Bot:", output)

        logger.log("FINAL_RESPONSE", {"response": output})

        # SAVE MEMORY AFTER INTERACTION
        history.append({
            "user": user_input,
            "bot": output
        })

        save_memory(history)

        logger.log("MEMORY_SAVED", {
            "history_length": len(history),
            "trigger": "interaction"
        })

        # 💾 Persist logs every turn
        logger.save()


if __name__ == "__main__":
    main()
