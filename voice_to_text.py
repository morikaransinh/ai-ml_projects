#!/usr/bin/env python3
"""
emergency_local.py
Records audio from the default microphone until ENTER is pressed,
saves as 16 kHz mono WAV, uploads to Google Gemini (via google-generativeai),
gets transcription and a simple emergency analysis (JSON or SAFE).
"""

import os
import tempfile
import sys
import time
from typing import Optional

import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy.io import wavfile
import google.generativeai as genai
from colorama import init as colorama_init, Fore, Style
from dotenv import load_dotenv

colorama_init()
load_dotenv()  # loads .env if present

# Read API key from environment
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print(Fore.RED + "ERROR: No GEMINI_API_KEY found in environment." + Style.RESET_ALL)
    print("Set GEMINI_API_KEY as an environment variable or create a .env file.")
    sys.exit(1)

# Configure Gemini
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")  # use flash/pro per your access

# Recording params
TARGET_SR = 16000
CHANNELS = 1
SUBTYPE = "PCM_16"  # write 16-bit PCM WAV


def record_until_enter(sr: int = TARGET_SR, channels: int = CHANNELS) -> str:
    """
    Records audio from microphone until user presses ENTER.
    Saves to a temporary WAV file (16-bit PCM, TARGET_SR) and returns path.
    """
    print(Fore.CYAN + "🎙️ Recording... Press ENTER to stop." + Style.RESET_ALL)
    frames = []

    def callback(indata, frames_count, time_info, status):
        if status:
            print("Record status:", status, file=sys.stderr)
        # indata is float32 with shape (frames_count, channels)
        frames.append(indata.copy())

    with sd.InputStream(samplerate=sr, channels=channels, callback=callback):
        try:
            input()  # wait until user presses ENTER
        except KeyboardInterrupt:
            print("\nInterrupted by user.")
    if not frames:
        raise RuntimeError("No audio captured. Check microphone.")

    audio = np.concatenate(frames, axis=0)

    # Ensure shape (n_samples, channels)
    if audio.ndim == 1:
        audio = audio[:, None]

    # Convert to 16-bit PCM and write using soundfile for robust sample rates
    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp_path = tmpfile.name
    tmpfile.close()

    # Write with soundfile to ensure correct subtype & sr
    sf.write(tmp_path, audio, sr, subtype=SUBTYPE)
    print(Fore.YELLOW + f"Saved recording to: {tmp_path}" + Style.RESET_ALL)
    return tmp_path


def transcribe_with_gemini(wav_path: str) -> str:
    """
    Uploads the wav file to Gemini and returns transcription text.
    """
    print("⏳ Uploading audio to Gemini...")
    try:
        response = model.generate_content([genai.upload_file(wav_path)])
    except Exception as e:
        print(Fore.RED + "Error calling Gemini:" + Style.RESET_ALL, e)
        raise

    # Try to safely extract text
    text = None
    # many SDK versions return object with .text; handle dicts/strings too
    if hasattr(response, "text"):
        text = response.text
    elif isinstance(response, dict):
        text = response.get("text") or response.get("output") or str(response)
    else:
        text = str(response)

    if not text:
        raise RuntimeError("No transcription text returned by Gemini.")
    return text.strip()


def analyze_emergency(text: str) -> str:
    """
    Sends a prompt to Gemini to detect if the transcription indicates an emergency.
    Returns the raw model output (expected: JSON or the string SAFE).
    """
    prompt = f"""
You are an AI for a Tourist Emergency Alert System.

Transcription: "{text}"

Task:
- If this is an emergency, output JSON in this exact format:
{{ 
  "start": 0,
  "end": 2,
  "label": "<short emergency type: e.g. 'Wild animal chase', 'Accident', 'Medical help', 'Robbery'>",
  "details": "<brief explanation of the emergency>"
}}
- If it's safe, output: SAFE

Only output the JSON or the single word SAFE, and nothing else.
"""
    try:
        response = model.generate_content(prompt)
    except Exception as e:
        print(Fore.RED + "Error calling Gemini for analysis:" + Style.RESET_ALL, e)
        raise

    if hasattr(response, "text"):
        return response.text.strip()
    return str(response).strip()


def main_loop():
    print(Fore.MAGENTA + "=== Local Emergency Detector ===" + Style.RESET_ALL)
    print("Press ENTER to start recording a clip. Press Ctrl+C to exit.\n")

    try:
        while True:
            input(Fore.BLUE + "Press ENTER to start recording..." + Style.RESET_ALL)
            wav_path = record_until_enter()
            try:
                transcript = transcribe_with_gemini(wav_path)
            except Exception as e:
                print(Fore.RED + "Transcription failed:" + Style.RESET_ALL, e)
                continue

            print(Fore.GREEN + "\n📝 Transcription:" + Style.RESET_ALL, transcript)

            try:
                analysis = analyze_emergency(transcript)
            except Exception as e:
                print(Fore.RED + "Emergency analysis failed:" + Style.RESET_ALL, e)
                continue

            # Interpret analysis
            if "SAFE" in analysis.upper():
                print(Fore.GREEN + "✅ No emergency detected." + Style.RESET_ALL)
            else:
                print(Fore.RED + Style.BRIGHT + "\n📢 ALERT (raw model output):" + Style.RESET_ALL)
                print(Fore.RED + analysis + Style.RESET_ALL)
                print(Fore.RED + Style.BRIGHT + "🚨 EMERGENCY ALERT! Take action!" + Style.RESET_ALL)

            # remove temp file
            try:
                os.remove(wav_path)
            except Exception:
                pass

            print("\n--- Ready for next recording ---\n")

    except KeyboardInterrupt:
        print("\nExiting. Stay safe!")
        return


if __name__ == "__main__":
    main_loop()
