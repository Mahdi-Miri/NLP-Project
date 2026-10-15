import argparse
import os
import sys
import tempfile
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import config
from src.step1_graph.autocomplete import QuoteAutocompleter
from src.step1_graph.graph_db import get_quote_graph
from src.step2_voice.chatbot import WhichQuoteChatbot
from src.utils.audio_utils import record_audio, play_audio


def print_banner():
    print(r"""
  ==============================================================
    Corso di Natural Language Processing - University Project
    Step 1: Wikiquote Graph Database & Autocompleter
    Step 2: "Which Quote?" Interactive Voice Conversational Agent
  ==============================================================
    """)


def run_step1_demo():
    """Interactive demo for Step 1 Autocompletion."""
    print("\n--- STEP 1: Wikiquote Citation Autocompleter ---")
    print("Enter a partial quote (e.g. 'To be', 'Stay hungry', 'Imagination is', 'Darkness').")
    print("Type 'exit' to return to the main menu.\n")

    ac = QuoteAutocompleter()

    while True:
        try:
            query = input("Enter quote prefix > ").strip()
            if not query or query.lower() in ["exit", "quit", "q"]:
                break

            results = ac.autocomplete(query, top_k=3)
            if not results:
                print("  [!] No matching quote found. Try another phrase or populate more data.")
                continue

            print(f"\n  Found {len(results)} matching citation(s):")
            for idx, r in enumerate(results, 1):
                print(f"  [{idx}] Quote: \"{r['full_quote']}\"")
                print(f"      Author: {r['author']}")
                print(f"      Source: {r['source']}")
                print(f"      Work:   {r['work']}\n")
        except (KeyboardInterrupt, EOFError):
            break


def run_step2_voice_demo():
    """Interactive demo for Step 2 Voice Conversation."""
    print("\n--- STEP 2: 'Which Quote?' Interactive Voice System ---")
    print("This mode records your voice command, identifies the speaker,")
    print("transcribes the speech, and responds with a personalized voice.")
    print("Type 'exit' when prompted to return to main menu.\n")

    chatbot = WhichQuoteChatbot()
    registered_speakers = chatbot.speaker_system.list_users()

    print(f"[*] Registered Speakers: {registered_speakers if registered_speakers else 'None (Guests only)'}")

    while True:
        try:
            cmd = input("\nPress ENTER to record 4s of voice command (or 'exit' to quit): ").strip()
            if cmd.lower() in ["exit", "quit", "q"]:
                break

            temp_audio = os.path.join(tempfile.gettempdir(), "user_voice_command.wav")
            record_audio(temp_audio, duration=4.0)

            print("[*] Processing voice command turn...")
            turn_result = chatbot.process_voice_turn(temp_audio)

            print("\n" + "=" * 50)
            print(f"  [Speaker ID]    : {turn_result['speaker']} (confidence: {turn_result['confidence']})")
            print(f"  [Transcribed]   : \"{turn_result['transcription']}\"")
            print(f"  [Response Text] : \"{turn_result['response']}\"")
            print(f"  [Voice Used]    : {turn_result['voice_used']}")
            print("=" * 50)

            # Play back vocal response
            if turn_result.get("audio_response_path") and os.path.exists(turn_result["audio_response_path"]):
                print("[*] Playing personalized voice response...")
                play_audio(turn_result["audio_response_path"])

        except (KeyboardInterrupt, EOFError):
            break


def run_step2_text_demo():
    """Interactive text chat demo for Step 2."""
    print("\n--- STEP 2: 'Which Quote?' Conversational Chatbot (Text Mode) ---")
    print("Ask for quote autocompletions, attribution ('Who said...'), or play 'quiz'.")
    print("Type 'exit' to quit.\n")

    chatbot = WhichQuoteChatbot()

    # Allow simulating different registered users
    speaker_name = input("Enter current speaker identity (default 'Guest'): ").strip() or "Guest"

    while True:
        try:
            user_msg = input(f"\n[{speaker_name}] > ").strip()
            if not user_msg or user_msg.lower() in ["exit", "quit", "q"]:
                break

            reply = chatbot.process_text_turn(user_msg, speaker_name=speaker_name)
            print(f"[Which Quote Assistant] > {reply}")
        except (KeyboardInterrupt, EOFError):
            break


def show_database_stats():
    """Displays current database statistics."""
    graph = get_quote_graph()
    stats = graph.get_stats()
    print("\n--- Wikiquote Graph Database Statistics ---")
    print(f"  Total Quotes     : {stats.get('quotes', 0)}")
    print(f"  Total Authors    : {stats.get('authors', 0)}")
    print(f"  Total Works      : {stats.get('works', 0)}")
    print(f"  Total Categories : {stats.get('categories', 0)}")
    print("-------------------------------------------\n")


def main():
    parser = argparse.ArgumentParser(description="NLP Project - Wikiquote Graph & Voice Agent")
    parser.add_argument("--step", choices=["1", "2", "text", "stats"], help="Directly jump to a step demo")
    args = parser.parse_args()

    print_banner()

    if args.step == "1":
        run_step1_demo()
        return
    elif args.step == "2":
        run_step2_voice_demo()
        return
    elif args.step == "text":
        run_step2_text_demo()
        return
    elif args.step == "stats":
        show_database_stats()
        return

    while True:
        print("\nPlease select an option:")
        print("  [1] Step 1: Wikiquote Graph Autocompletion Demo")
        print("  [2] Step 2: 'Which Quote?' Voice Agent (Live Mic + Speaker ID + TTS)")
        print("  [3] Step 2: 'Which Quote?' Chatbot (Text Console Mode)")
        print("  [4] Register / Enroll a New Speaker Profile")
        print("  [5] View Graph Database Statistics")
        print("  [6] Exit")

        choice = input("\nEnter choice [1-6]: ").strip()
        if choice == "1":
            run_step1_demo()
        elif choice == "2":
            run_step2_voice_demo()
        elif choice == "3":
            run_step2_text_demo()
        elif choice == "4":
            from scripts.enroll_speaker import enroll_speaker_cli
            enroll_speaker_cli()
        elif choice == "5":
            show_database_stats()
        elif choice in ["6", "exit", "quit", "q"]:
            print("\nExiting. Good luck with the NLP presentation!")
            break
        else:
            print("[!] Invalid option. Please enter 1-6.")


if __name__ == "__main__":
    main()
