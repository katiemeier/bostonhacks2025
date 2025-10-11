import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from resemblyzer import VoiceEncoder, preprocess_wav
from pathlib import Path
from numpy import dot
from numpy.linalg import norm
import os

# Absolute path to the repo's audio directory (../audio relative to this file)
AUDIO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "audio"))

# === Step 1: Record audio ===
def record_voice(filename, duration=3, fs=16000):
    # Recording with sounddevice; this function is synchronous
    print(f"🎤 Recording for {duration} seconds...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    write(filename, fs, audio)
    print(f"✅ Saved as {filename}")

# === Step 2: Compute speaker embedding ===
def get_embedding(filename):
    encoder = VoiceEncoder()
    wav = preprocess_wav(Path(filename))
    return encoder.embed_utterance(wav)

# === Step 3: Compare embeddings ===
def similarity(a, b):
    return dot(a, b) / (norm(a) * norm(b))

# === Step 4: Enrollment ===
def enroll():
    try:
        auth_path = os.path.join(AUDIO_DIR, "authorized.wav")
        # Ensure audio directory exists
        os.makedirs(AUDIO_DIR, exist_ok=True)
        record_voice(auth_path, duration=3)
        print("Your voice password is saved! 🗝️")
        return True
    except Exception as e:
        print(f"Enrollment failed: {e}")
        return False

# === Step 5: Verification ===
def verify():
    import threading
    result_container = {}

    def worker():
        auth_path = os.path.join(AUDIO_DIR, "authorized.wav")
        if not os.path.exists(auth_path):
            msg = "No authorized voice found! Please enroll first."
            print(msg)
            result_container["result"] = {"status": "no_enrollment", "message": msg}
            return
        try:
            attempt_path = os.path.join(AUDIO_DIR, "attempt.wav")
            record_voice(attempt_path, duration=3)
            authorized = get_embedding(auth_path)
            attempt = get_embedding(attempt_path)
            score = similarity(authorized, attempt)
            print(f"🔍 Voice similarity score: {score:.3f}")
            if score > 0.60:
                print("✅ Access Granted! Your secret journal is unlocked 💖")
                try:
                    from src.play_sound import play_sound
                    jingle_path = os.path.join(AUDIO_DIR, "jingle.wav")
                    # Debug logging to verify resolved path and existence
                    print(f"Attempting to play unlock sound at: {jingle_path}")
                    print(f"Unlock sound exists? {os.path.exists(jingle_path)}")
                    if not os.path.exists(jingle_path):
                        # Fallback: try from current working directory
                        cwd_fallback = os.path.join(os.getcwd(), "audio", "jingle.wav")
                        print(f"Primary jingle not found. Trying fallback: {cwd_fallback}")
                        jingle_path = cwd_fallback
                    play_sound(jingle_path)
                except Exception as e:
                    print(f"Could not play unlock sound: {e}")
                result_container["result"] = {"status": "granted", "score": float(score)}
            else:
                print("❌ Access Denied! Voice does not match.")
                result_container["result"] = {"status": "denied", "score": float(score)}
        except Exception as e:
            print(f"Verification failed: {e}")
            result_container["result"] = {"status": "error", "message": str(e)}

    t = threading.Thread(target=worker)
    t.start()
    t.join()
    return result_container.get("result")

def _authorized_exists():
    auth_path = os.path.join(AUDIO_DIR, "authorized.wav")
    return os.path.exists(auth_path)

# === Step 6: Simple menu ===
def main():
    while True:
        print("\n--- Secret Voice Journal ---")
        print("1. Enroll voice password")
        print("2. Try to unlock")
        print("3. Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            enroll()
        elif choice == "2":
            verify()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
