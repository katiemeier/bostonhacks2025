import os
import platform
import subprocess

def play_sound(sound_path):
    if not os.path.exists(sound_path):
        print(f"Sound file not found: {sound_path}")
        return
    if platform.system() == "Windows":
        import winsound
        winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    else:
        # Prefer macOS native player to avoid C-extension crashes
        if platform.system() == "Darwin":
            try:
                subprocess.Popen(["afplay", sound_path])
                return
            except Exception:
                pass
        # Fallback: use simpleaudio if available
        try:
            import simpleaudio
            wave_obj = simpleaudio.WaveObject.from_wave_file(sound_path)
            wave_obj.play()
        except Exception as e:
            print(f"Could not play sound: {e}")
