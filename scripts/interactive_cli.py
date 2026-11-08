import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.dialogue.chatbot import NeapolitanArtChatbot


def main():
    print("=" * 65)
    print("Neapolitan Art Conversational System (Academic CLI)")
    print("Works by Caravaggio & Battistello Caracciolo in Naples")
    print("Type 'exit' or 'quit' to terminate. Type 'reset' to clear context.")
    print("=" * 65)

    bot = NeapolitanArtChatbot()

    while True:
        try:
            user_input = input("\nUser > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print("Session ended.")
                break
            if user_input.lower() == "reset":
                bot.reset_dialogue()
                print("Dialogue context reset to initial state.")
                continue

            result = bot.process_utterance(user_input)

            if result.inconsistency_report.is_inconsistent:
                inc = result.inconsistency_report
                print(f"\n[INCONSISTENCY DETECTED: {inc.inconsistency_type.value.upper()}]")
                print(f"Explanation: {inc.explanation}")
                print(f"Correction: {inc.suggested_correction}")

            print(f"\nSystem Response:\n{result.system_response}")
            print(f"\n[Dialogue State: Artist='{result.active_artist}', Artwork='{result.active_artwork}', Location='{result.active_location}']")

        except KeyboardInterrupt:
            print("\nExiting...")
            break


if __name__ == "__main__":
    main()
