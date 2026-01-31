import os
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import streamlit as st

# Cache use kar rahe hai taaki bar bar keys load na karni pade
@st.cache_data(show_spinner=False)
def get_api_keys():
    """
    Gemini API keys load karne ke liye function.
    Pehle secrets check karega fir env variables.
    """
    # Local development ke liye .env file try kar rahe hai
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Set use kiya hai taaki duplicate keys na aaye
    keys = set()
    try:
        if "GEMINI_API_KEY_1" in st.secrets: keys.add(st.secrets["GEMINI_API_KEY_1"])
        if "GEMINI_API_KEY_2" in st.secrets: keys.add(st.secrets["GEMINI_API_KEY_2"])
        if "GEMINI_API_KEY_3" in st.secrets: keys.add(st.secrets["GEMINI_API_KEY_3"])
        if "GEMINI_API_KEY_4" in st.secrets: keys.add(st.secrets["GEMINI_API_KEY_4"])
    except st.errors.StreamlitAPIException:
        pass
    # Environment variables check karne ke liye
    if os.getenv("GEMINI_API_KEY_1"): keys.add(os.getenv("GEMINI_API_KEY_1"))
    if os.getenv("GEMINI_API_KEY_2"): keys.add(os.getenv("GEMINI_API_KEY_2"))
    if os.getenv("GEMINI_API_KEY_3"): keys.add(os.getenv("GEMINI_API_KEY_3"))
    if os.getenv("GEMINI_API_KEY_4"): keys.add(os.getenv("GEMINI_API_KEY_4"))
    
    return [k for k in keys if k]

def generate_with_failover(prompt: str, model_name: str = "gemini-2.5-flash-lite", file_name: str | None = None, system_instruction: str | None = None) -> str:
    """
    Content generate karne ke liye function.
    Agar ek key limit reach kar jaye to dusri use karega (Failover logic).
    """
    # Keys load karne ke liye
    api_keys = get_api_keys()
    if not api_keys:
        return "ERROR: No API keys configured."

    # Har key try karke dekhenga jab tak ek key work nhi kre 
    for key in api_keys:
        try:
            # API key set karge if key mil jaayegi toh 
            genai.configure(api_key=key)
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction
            )

            # Content prepare karne ke liye 
            content = [prompt]
            if file_name:
                content.insert(0, genai.get_file(file_name))

            resp = model.generate_content(content)
            return (resp.text or "").strip() or "ERROR: Empty response from model."
        except google_exceptions.ResourceExhausted:
            # Agar quota khatam ho jaaye to next key try karega <heart of tis project to keep it free >
            continue
        except Exception as e:
            return f"ERROR: An unexpected error occurred: {e}"

    return "ERROR: All API keys are currently rate-limited. Please wait and try again."