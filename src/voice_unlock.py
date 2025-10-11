import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from resemblyzer import VoiceEncoder, preprocess_wav
from pathlib import Path
from numpy import dot
from numpy.linalg import norm
import os

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
        record_voice("authorized.wav", duration=3)
        print("Your voice password is saved! 🗝️")
        return True
    except Exception as e:
        print(f"Enrollment failed: {e}")
        return False

# === Step 5: Verification ===
def verify():
    if not os.path.exists("authorized.wav"):
        msg = "No authorized voice found! Please enroll first."
        print(msg)
        return {"status": "no_enrollment", "message": msg}

    try:
        record_voice("attempt.wav", duration=3)

        authorized = get_embedding("authorized.wav")
        attempt = get_embedding("attempt.wav")
        score = similarity(authorized, attempt)

        print(f"🔍 Voice similarity score: {score:.3f}")
        if score > 0.85:
            print("✅ Access Granted! Your secret journal is unlocked 💖")
            return {"status": "granted", "score": float(score)}
        else:
            print("❌ Access Denied! Voice does not match.")
            return {"status": "denied", "score": float(score)}
    except Exception as e:
        print(f"Verification failed: {e}")
        return {"status": "error", "message": str(e)}

def _authorized_exists():
    return os.path.exists("authorized.wav")

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
