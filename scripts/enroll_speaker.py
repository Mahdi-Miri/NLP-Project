import argparse
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import config
from src.step2_voice.speaker_id import SpeakerIdentificationSystem
from src.utils.audio_utils import record_audio

AVAILABLE_VOICES = {
    "1": ("en-US-GuyNeural", "Male (US, Natural)"),
    "2": ("en-US-JennyNeural", "Female (US, Friendly)"),
    "3": ("en-GB-RyanNeural", "Male (UK, Formal)"),
    "4": ("en-GB-SoniaNeural", "Female (UK, Elegant)"),
    "5": ("en-AU-WilliamNeural", "Male (Australian, Casual)"),
}


def enroll_speaker_cli():
    print("=" * 60)
    print("      SPEAKER ENROLLMENT - 'WHICH QUOTE?' SYSTEM")
    print("=" * 60)

    name = input("Enter speaker name (e.g. Mahdi): ").strip()
    if not name:
        print("[!] Error: Name cannot be blank.")
        return

    print("\nSelect voice response preference for this speaker:")
    for key, (v_id, label) in AVAILABLE_VOICES.items():
        print(f"  [{key}] {label} ({v_id})")

    choice = input("Enter choice (1-5, default 1): ").strip() or "1"
    voice_selected = AVAILABLE_VOICES.get(choice, AVAILABLE_VOICES["1"])[0]

    rate = input("Speaking rate adjustment (e.g. +0%, +10%, -10%, default +0%): ").strip() or "+0%"
    pitch = input("Pitch adjustment (e.g. +0Hz, +5Hz, -5Hz, default +0Hz): ").strip() or "+0Hz"

    voice_pref = {
        "voice": voice_selected,
        "rate": rate,
        "pitch": pitch
    }

    # Audio input option
    print("\nHow would you like to provide the enrollment audio sample?")
    print("  [1] Record live via microphone (4 seconds)")
    print("  [2] Provide path to an existing .wav audio file")

    audio_opt = input("Choice (1 or 2): ").strip() or "1"

    audio_path = config.paths.audio_dir / f"{name.lower()}_enrollment.wav"

    if audio_opt == "1":
        print(f"[*] Preparing microphone... Say a sentence like: 'Hello, my name is {name} and this is my voice.'")
        input("Press ENTER when ready to record...")
        record_audio(str(audio_path), duration=4.0)
    else:
        existing_path = input("Enter path to WAV file: ").strip()
        if not Path(existing_path).exists():
            print(f"[!] Error: File '{existing_path}' does not exist.")
            return
        audio_path = Path(existing_path)

    speaker_sys = SpeakerIdentificationSystem()
    profile = speaker_sys.register_user(name, str(audio_path), voice_preference=voice_pref)

    print("\n[+] Speaker enrolled successfully!")
    print(f"    Name: {profile['name']}")
    print(f"    Preferred Voice: {profile['voice_preference']['voice']}")
    print(f"    Voice Rate: {profile['voice_preference']['rate']}")
    print(f"    Voice Pitch: {profile['voice_preference']['pitch']}")


def main():
    parser = argparse.ArgumentParser(description="Enroll a speaker voice profile.")
    parser.add_argument("--name", type=str, help="Speaker name")
    parser.add_argument("--audio", type=str, help="Audio file path")
    parser.add_argument("--voice", type=str, default="en-US-GuyNeural", help="TTS voice ID")
    args = parser.parse_args()

    if args.name and args.audio:
        speaker_sys = SpeakerIdentificationSystem()
        speaker_sys.register_user(args.name, args.audio, {"voice": args.voice, "rate": "+0%", "pitch": "+0Hz"})
    else:
        enroll_speaker_cli()


if __name__ == "__main__":
    main()
