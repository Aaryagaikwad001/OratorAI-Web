import streamlit as st
import requests
import json
# gtts is included but not used, kept for dependency consistency if needed later
from gtts import gTTS 
from io import BytesIO
import speech_recognition as sr
import librosa
import numpy as np
from pydub import AudioSegment
import tempfile
import os

# ---------------- 1. PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND) ----------------
st.set_page_config(page_title="OratorAI 🎤", page_icon="🎤", layout="centered")


# ---------------- 2. AESTHETIC STYLING ----------------
st.markdown("""
<style>
/* Main Content Font */
html, body, [class*="stText"] {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 16px;
    line-height: 1.6;
}

/* Header/Title Font - CHANGED TO DARK NAVY BLUE (#1E3A8A) */
h1 {
    font-size: 2.5em; 
    color: #1E3A8A; /* Dark Navy Blue */
    margin-bottom: 0.5em;
}

/* Subheader Styling for Script/Voice Analysis (Sea Green) */
h2 {
    color: #2e8b57; /* Sea Green */
    border-bottom: 2px solid #2e8b57;
    padding-bottom: 5px;
    margin-top: 25px; 
}

/* Clean up extra spacing in markdown outputs */
.stMarkdown {
    white-space: pre-wrap !important;
    padding-top: 5px;
    padding-bottom: 5px;
}
</style>
""", unsafe_allow_html=True)


# ---------------- 3. APP HEADER ----------------
st.title("🎤 OratorAI — Complete Anchor Assistant")
st.caption("Generate your script, and get professional feedback on your voice delivery.")
st.markdown("---")

# ---------------- 4. GEMINI API KEY & FUNCTION ----------------
# IMPORTANT: PASTE YOUR VALID GEMINI API KEY HERE
GEMINI_API_KEY = "AIzaSyBC_99zuV8wf-OHeWxrjIvrJf7RsVYtFgI"

def call_gemini(prompt_text):
    # This check ensures the user has provided a key. It must check against the placeholder.
    if not GEMINI_API_KEY or GEMINI_API_KEY == "PASTE_YOUR_ACTUAL_GEMINI_API_KEY_HERE":
        raise ValueError("API key missing. Please paste your valid key in GEMINI_API_KEY.")
    
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

    body = {"contents": [{"parts": [{"text": prompt_text}]}]}
    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=60)
        resp.raise_for_status() 
        data = resp.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"API Request Failed: {e}")

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return json.dumps(data, indent=2)

# ---------------- 5. SCRIPT GENERATOR ----------------
st.header("✍️ Script Generator")

with st.form("script_form"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        event = st.selectbox("Event Type", ["Wedding", "College Fest", "Farewell", "Corporate", "Seminar", "Cultural Program", "Other"])
    with col2:
        tone = st.selectbox("Tone / Style", ["Formal", "Emotional", "Funny", "Inspirational", "Casual"])
    with col3:
        time_of_day = st.selectbox("Time of Day", ["Morning", "Afternoon", "Evening", "Night"])
        
    names = st.text_input("Names to mention (comma separated) — optional (e.g., Chief Guest, Principal)", key="names_input")
    extra = st.text_area("Extra notes (optional) — Specify topics, specific theme, etc.", height=80, key="notes_area")
    
    st.markdown("---")
    generate = st.form_submit_button("✨ Generate Script + Delivery Guide")

if generate:
    st.info("Generating your script... please wait ⏳")

    # PROMPT UPDATED: Asking for a very short, concise guide
    prompt = f"""
You are a professional stage anchor coach. Your output must be formatted using **Markdown** for clarity and professional look.

Task 1️⃣: Create an anchor script for the following event:
- Event: {event}
- Tone: {tone}
- Time: {time_of_day}
- Names: {names}
- Notes: {extra}

Task 2️⃣: After writing the script, provide a **very short and concise** delivery guide (no more than 4 bullet points) with pauses, emotions, and expression tips. This guide MUST be provided as a **bulleted list** using Markdown.
Avoid writing “Language: Indian English” anywhere. 
Keep it simple and naturally readable for Indian audiences.
    """

    try:
        output = call_gemini(prompt)
        st.success("✅ Script and Delivery Guide Generated Successfully!")

        st.subheader("🎬 Anchor Script + Delivery Guide")
        st.markdown(output)
        st.session_state["script_text"] = output

    except Exception as e:
        st.error("⚠️ API call failed: " + str(e))

# ---------------- 6. VOICE UPLOAD FOR FEEDBACK ----------------
st.markdown("---")
st.header("🎙️ Upload Your Speech for Feedback")

uploaded_audio = st.file_uploader(
    "Upload your recorded speech (any format: MP3, WAV, M4A, OGG, FLAC, AAC, etc.)",
    type=["mp3", "wav", "m4a", "ogg", "flac", "aac"]
)

# --- AUDIO PROCESSING FUNCTIONS ---
def convert_to_wav(uploaded_audio):
    temp_dir = tempfile.mkdtemp()
    original_path = os.path.join(temp_dir, uploaded_audio.name)
    with open(original_path, "wb") as f:
        f.write(uploaded_audio.read())
    # NOTE: pydub requires external ffmpeg dependency to handle m4a/mp3 etc.
    audio = AudioSegment.from_file(original_path)
    wav_path = os.path.join(temp_dir, "converted.wav")
    audio.export(wav_path, format="wav")
    return wav_path

def analyze_audio(file):
    data, sr = librosa.load(file, sr=None)
    duration = librosa.get_duration(y=data, sr=sr)
    tempo, _ = librosa.beat.beat_track(y=data, sr=sr)
    rms = np.mean(librosa.feature.rms(y=data))
    return duration, tempo, rms

def transcribe_audio(file):
    r = sr.Recognizer()
    try:
        with sr.AudioFile(file) as source:
            audio = r.record(source)
            return r.recognize_google(audio, language='en-IN')
    except sr.UnknownValueError:
        return "(Unable to clearly understand audio)"
    except sr.RequestError:
        return "(Could not request results from Google Speech Recognition service)"
# --- END AUDIO PROCESSING FUNCTIONS ---

if uploaded_audio is not None:
    st.audio(uploaded_audio)
    st.info("Processing your file... please wait 🔍")

    try:
        wav_file = convert_to_wav(uploaded_audio)
        duration, tempo, rms = analyze_audio(wav_file)
        transcript = transcribe_audio(wav_file)

        # Fix the numpy array to float conversion
        try:
            tempo_value = float(tempo[0]) 
        except (TypeError, IndexError):
            tempo_value = float(tempo) if isinstance(tempo, (float, int)) else 0.0

        st.subheader("📊 Voice Analysis")
        st.write(f"🎧 **Duration:** {duration:.1f} sec")
        st.write(f"🎵 **Tempo:** {tempo_value:.1f} BPM") 
        st.write(f"🔊 **Loudness:** {rms:.4f}")
        st.write(f"🗣️ **Transcription:** {transcript}")

        # Use tempo_value and format the prompt to request a bulleted list
        feedback_prompt = f"""
You are a speech and communication coach. Analyze this voice recording and give 5 quick, practical improvement suggestions based on clarity, tone, pauses, energy, pronunciation, and confidence.

Provide your output ONLY as a **bulleted list** using Markdown. Do not include any introductory or concluding text.

---
Input Data:
Transcript: {transcript}
Duration: {duration:.1f}s
Tempo: {tempo_value:.1f} BPM
Loudness: {rms:.4f}
---
"""

        try:
            feedback = call_gemini(feedback_prompt)
            st.subheader("🎯 AI Feedback & Improvement Tips")
            st.markdown(feedback)
        except Exception as e:
            st.error("⚠️ Could not fetch AI feedback: " + str(e))
    
    except Exception as e:
        st.error(f"An error occurred during file processing or analysis: {e}")

# ---------------- Hide Streamlit Footer/Menu ----------------
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)   