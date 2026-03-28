import streamlit as st
from groq import Groq
import google.generativeai as genai
from duckduckgo_search import DDGS
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="JARVIS AI", page_icon="🤖", layout="wide")

# --- CUSTOM CSS (Same Beautiful Look) ---
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #ffffff; }
    .main-title { font-size: 3rem !important; font-weight: 800; background: linear-gradient(90deg, #00d2ff, #3a7bd5); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .stChatMessage { background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 15px; margin-bottom: 10px; backdrop-filter: blur(10px); }
    [data-testid="stChatMessage"][aria-label*="user"] { border-left: 4px solid #00d2ff; }
    [data-testid="stChatMessage"][aria-label*="assistant"] { border-left: 4px solid #3a7bd5; }
    .stChatInput > div > div > div { background-color: rgba(255, 255, 255, 0.1) !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; border-radius: 25px !important; }
    .stChatInput input { color: white !important; }
    section[data-testid="stSidebar"] { background-color: rgba(26, 26, 46, 0.95); border-right: 1px solid rgba(255,255,255,0.1); }
    .stButton button { background: linear-gradient(90deg, #00d2ff, #3a7bd5); color: white; border: none; border-radius: 20px; font-weight: bold; }
    .status-box { background-color: rgba(0, 0, 0, 0.3); padding: 10px; border-radius: 10px; border-left: 3px solid #00d2ff; margin: 10px 0; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
GROQ_KEY = "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"
GEMINI_KEY = "AIzaSyD0mlq3W9veyvc-9piMFgAypx8KCjdLc4w"

# --- CLIENT INITIALIZATION (Robust) ---
@st.cache_resource
def init_models():
    # 1. Initialize Groq
    groq_c = None
    try:
        groq_c = Groq(api_key=GROQ_KEY)
    except Exception as e:
        print(f"Groq Init Error: {e}")

    # 2. Initialize Gemini
    gemini_m = None
    try:
        genai.configure(api_key=GEMINI_KEY)
        # SAHI MODEL NAME: 'gemini-1.5-flash' (Not latest)
        gemini_m = genai.GenerativeModel('gemini-1.5-flash') 
    except Exception as e:
        print(f"Gemini Init Error: {e}")
        
    return groq_c, gemini_m

groq_client, gemini_model = init_models()

# --- MEMORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- TOOLS ---
def search_internet_tool(query):
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
        context = "\n".join([f"Source: {r['title']}\nInfo: {r['body']}" for r in results])
        return context
    except:
        return "Search unavailable."

# --- MAIN BRAIN ---
def get_response(user_prompt):
    # Check Internet
    search_keywords = ["news", "latest", "live", "weather", "market", "price"]
    need_search = any(word in user_prompt.lower() for word in search_keywords)
    
    context_data = ""
    if need_search:
        with st.spinner("🌐 Scanning the Web..."):
            context_data = search_internet_tool(user_prompt)

    system_prompt = "You are JARVIS, an advanced AI assistant. Be precise."
    final_prompt = user_prompt
    
    if context_data:
        final_prompt = f"User Question: {user_prompt}\n\nLive Data:\n{context_data}\n\nAnswer based on data."

    messages_hist = [{"role": "system", "content": system_prompt}] + st.session_state.messages + [{"role": "user", "content": final_prompt}]

    # PRIORITY 1: GROQ (FAST)
    if groq_client:
        try:
            res = groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=messages_hist
            )
            return res.choices[0].message.content, "🚀 Groq Llama 3", True
        except Exception as e:
            # Agar Groq fail ho jaye to Gemini try karega
            pass

    # PRIORITY 2: GEMINI (BACKUP)
    if gemini_model:
        try:
            # Gemini simple text prompt leta hai
            res = gemini_model.generate_content(final_prompt)
            return res.text, "💡 Gemini 1.5 Flash", True
        except Exception as e:
            return f"❌ Gemini Error: {str(e)}", "❌ Error", False

    return "All systems offline.", "❌ Offline", False

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2>⚡ Control Panel</h2>", unsafe_allow_html=True)
    if st.button("🗑️ Clear Memory"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("### 🧠 System Status")
    st.metric("Groq Engine", "🟢 Online" if groq_client else "🔴 Offline")
    st.metric("Gemini Core", "🟢 Online" if gemini_model else "🔴 Offline")

# --- MAIN UI ---
st.markdown('<h1 class="main-title">J.A.R.V.I.S</h1>', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Command de..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            response, model_name, success = get_response(prompt)
            
            st.markdown(f"<div class='status-box'>Active Model: <b>{model_name}</b></div>", unsafe_allow_html=True)
            
            # Typewriter Effect
            placeholder = st.empty()
            full_text = ""
            for word in response.split():
                full_text += word + " "
                time.sleep(0.02)
                placeholder.markdown(full_text + "▌")
            placeholder.markdown(full_text)
            
            st.session_state.messages.append({"role": "assistant", "content": response})