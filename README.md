# bostonhacks2025

Secret voice-unlock journal (BostonHacks 2025)

This small app demonstrates a voice-based unlock for a private journal. The project uses a Tkinter GUI for the UI and the `resemblyzer` library for speaker embeddings.
## Inspiration
As kids, we all had a favorite novelty toy near and dear to our hearts, that as was we aged, were replaced with purely utilitarian apps that lacked the nostalgia and appeal of these original toys. One such beloved toy is the Mattel Secret Password Journal. We decided to bring the functionality and aesthetic of this toy into the modern age via digital application. 
## What it does
Our app takes a super-secret codeword from the user and saves it as a password that can only be inputted by the user’s unique voice. Users can then write to their hearts' content knowing their deepest secrets will be safe.
## How we built it
We built it with Python, using the Tkinter application to build out the app. We designed the graphics in Figma, and we used generative AI as support.
## Challenges we ran into
One of the first challenges we faced was incorporating the Figma designs into the Tkinter code. We solved this by downloading the Figma pages as PNGs, as then using them as the background image of the Home Page and Note interfaces. 
## Accomplishments That We're Proud Of
We are especially of being able to implement the voice functionality as we intended. The functionality is very similar to that of the physical Secret Password Journal, as you can make an initial password, change passwords, and unlock the journal with the current password. We are also proud of functionalities such as the blinking lights, the scroll bar in the Notes app, and other minor animations. Last, we are proud of adding a the ever-so-satisfying jingle when you unlock the journal and advance to the Notes page.
## What We Learned
A big thing was learned was navigating Git commands and using Git as a collaborative interface. We became comfortable with cloning repositories, creating branches, pushing and pulling code, and merging branches to Main. We also learned the basics of web app development, such as the Tkinter library and learning how to resize the interface depending on the size of the window. 
## What's next for Digital Secret Password Journal
Mainly, we hope to turn this application into a Desktop version, rather than being run through VS Code and Python.  Additionally, we hope to implement a fun cursor within the theme of the application, a Quit button in the Notes application, and of course, even more fun and juicy gossip!!!!!!!!


##Prerequisites
 - Python 3.8+
 - A working microphone and OS permissions for audio capture

Recommended (create a virtualenv first):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If you don't have a `requirements.txt`, install the main packages used by the project:

Required runtime libraries:
- tkinter (bundled with most Python distributions)
- numpy
- scipy
- sounddevice
- resemblyzer (will pull torch CPU by default)

Optional (improves UX/graphics/audio):
- Pillow (image scaling quality for GUI)
- simpleaudio (fallback audio player on non-macOS platforms)

Quick install (CPU-only):
```bash
pip install numpy scipy sounddevice resemblyzer Pillow simpleaudio
```
Note: On some platforms you may need to install PyTorch manually first for resemblyzer. See https://pytorch.org/get-started/locally/ for a wheel appropriate to your OS/CPU.

##Notes on platform support:
- On macOS you may need to allow microphone access the first time the app records.
- `resemblyzer` requires a working `torch` backend (it will pull a CPU-only wheel unless you install CUDA-enabled PyTorch).

##How to run

From the repository root:

```bash
python app.py
```

##Behavior
- On first run (no `authorized.wav` present) the launcher opens a small "Welcome / Set Voice Password" window where you record your voice password.
- After an authorized voice is present the app shows a locked landing page that only allows unlocking with voice or changing the password.
- When verification succeeds the app opens the notes application (from `src/noteapp.py`).

##Notes & Troubleshooting
- If recording fails, ensure your microphone is available and not used by another app.
- If `resemblyzer` import fails, install the `torch` wheel appropriate for your platform first (see PyTorch docs).
- If you want to reset the authorized voice, delete `authorized.wav` from the project root and re-run the app.

##Where To Edit
- GUI: `src/gui.py`
- Voice enrollment/verification: `src/voice_unlock.py`
- Notes app: `src/noteapp.py`

##Contact
- If you need any changes to the UX or add features (markdown preview, saving notes, etc.), open an issue or ask me here and I'll implement it.
