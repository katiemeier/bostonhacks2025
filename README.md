# bostonhacks2025

Secret voice-unlock journal (BostonHacks 2025)

This small app demonstrates a voice-based unlock for a private journal. The project uses a Tkinter GUI for the UI and the `resemblyzer` library for speaker embeddings.

Prerequisites
 - Python 3.8+
 - A working microphone and OS permissions for audio capture

Recommended (create a virtualenv first):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If you don't have a `requirements.txt`, install the main packages used by the project:

```bash
pip install markdown resemblyzer sounddevice scipy numpy
```

Notes on platform support:
- On macOS you may need to allow microphone access the first time the app records.
- `resemblyzer` requires a working `torch` backend (it will pull a CPU-only wheel unless you install CUDA-enabled PyTorch).

How to run

From the repository root:

```bash
python app.py
```

Behavior
- On first run (no `authorized.wav` present) the launcher opens a small "Welcome / Set Voice Password" window where you record your voice password.
- After an authorized voice is present the app shows a locked landing page that only allows unlocking with voice or changing the password.
- When verification succeeds the app opens the notes application (from `src/noteapp.py`).

Notes & troubleshooting
- If recording fails, ensure your microphone is available and not used by another app.
- If `resemblyzer` import fails, install the `torch` wheel appropriate for your platform first (see PyTorch docs).
- If you want to reset the authorized voice, delete `authorized.wav` from the project root and re-run the app.

Where to edit
- GUI: `src/gui.py`
- Voice enrollment/verification: `src/voice_unlock.py`
- Notes app: `src/noteapp.py`

Contact
- If you need any changes to the UX or add features (markdown preview, saving notes, etc.), open an issue or ask me here and I'll implement it.
