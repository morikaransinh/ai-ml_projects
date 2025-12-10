# import sounddevice as sd
# import scipy.io.wavfile as wav
# import numpy as np
# import google.generativeai as genai
# import tempfile

# # ⚠️ API Key directly in code (for demo only)
# API_KEY = "AIzaSyCotFhBkdXiH6RFh2wEtXdl7PftEOrqcSc"

# # Configure Gemini API
# genai.configure(api_key=API_KEY)
# model = genai.GenerativeModel("gemini-2.5-flash")  # or "gemini-2.5-pro"

# # Record audio until ENTER is pressed
# def record_audio():
#     fs = 16000  # sample rate
#     print("🎙️ Recording... Press ENTER to stop.")
#     recording = []

#     def callback(indata, frames, time, status):
#         if status:
#             print(status)
#         recording.append(indata.copy())

#     with sd.InputStream(samplerate=fs, channels=1, callback=callback):
#         input()  # waits until ENTER is pressed

#     audio_data = np.concatenate(recording, axis=0)

#     # Save temp wav file
#     tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
#     wav.write(tmpfile.name, fs, audio_data)
#     print(f"Saved recording: {tmpfile.name}")
#     return tmpfile.name

# # Send audio to Gemini and get transcription
# def transcribe(path):
#     print("⏳ Sending audio to Gemini...")
#     response = model.generate_content([genai.upload_file(path)])
#     print("✅ Transcription:", response.text)

# if __name__ == "__main__":
#     audio_path = record_audio()
#     transcribe(audio_path)

import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np
import google.generativeai as genai
import tempfile
import colorama
from colorama import Fore, Style


colorama.init()

# ⚠️ API Key (for demo only)
API_KEY = "AIzaSyCotFhBkdXiH6RFh2wEtXdl7PftEOrqcSc"

# Configure Gemini API
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")  # Pro = better reasoning

# Record audio until ENTER is pressed
def record_audio():
    fs = 16000
    print("🎙️ Recording... Press ENTER to stop.")
    recording = []

    def callback(indata, frames, time, status):
        if status:
            print(status)
        recording.append(indata.copy())

    with sd.InputStream(samplerate=fs, channels=1, callback=callback):
        input()

    audio_data = np.concatenate(recording, axis=0)

    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    wav.write(tmpfile.name, fs, audio_data)
    return tmpfile.name

# Transcribe speech
def transcribe(path):
    response = model.generate_content([genai.upload_file(path)])
    return response.text.strip()

# Detect emergency + provide structured JSON
def analyze_emergency(text):
    prompt = f"""
    You are an AI for a Tourist Emergency Alert System.

    Transcription: "{text}"

    Task:
    - If this is an emergency, output JSON in this exact format:
    ```json
    {{
      "start": 0,
      "end": 2,
      "label": "<short emergency type: e.g. 'Wild animal chase', 'Accident', 'Medical help', 'Robbery'>",
      "details": "<brief explanation of the emergency>"
    }}
    ```
    - If it's safe, output: SAFE
    """

    response = model.generate_content(prompt)
    return response.text.strip()

if __name__ == "__main__":
    while True:
        audio_path = record_audio()
        transcript = transcribe(audio_path)
        print(Fore.GREEN + f"\n📝 Transcription: {transcript}" + Style.RESET_ALL)

        analysis = analyze_emergency(transcript)

        if "SAFE" in analysis.upper():
            print(Fore.GREEN + "✅ No emergency detected.\n" + Style.RESET_ALL)
        else:
            print(Fore.RED + Style.BRIGHT + f"\n📢 ALERT: {analysis}\n" + Style.RESET_ALL)
            print(Fore.RED + Style.BRIGHT + "🚨 EMERGENCY ALERT! 🚨 Tourist needs help!\n" + Style.RESET_ALL)

        print("--- Ready for next recording ---\n")