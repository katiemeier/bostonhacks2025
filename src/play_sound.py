import os
import platform

def play_sound(sound_path):
    if not os.path.exists(sound_path):
        print(f"Sound file not found: {sound_path}")
        return
    if platform.system() == "Windows":
        import winsound
        winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    else:
        # For Mac/Linux, use simpleaudio or other cross-platform library
        try:
            import simpleaudio
            wave_obj = simpleaudio.WaveObject.from_wave_file(sound_path)
            wave_obj.play()
        except ImportError:
            print("simpleaudio not installed. Cannot play sound.")
