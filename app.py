import streamlit as st
from groq import Groq
import google.generativeai as genai
from duckduckgo_search import DDGS
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="JARVIS AI", page_icon="🤖", layout="wide")

# --- CUSTOM CSS (Sundar Design) ---
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%); color: #ffffff; }
    .main-title { font-size: 3rem !important; font-weight: 800; background: linear-gradient(90deg, #00d2ff, #3a7bd5); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .stChatMessage { background-color: rgba(255, 255, 255, 0.07); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 20px; margin-bottom: 15px; backdrop-filter: blur(10px); box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
    [data-testid="stChatMessage"][aria-label*="user"] { border-left: 5px solid #00d2ff; }
    [data-testid="stChatMessage"][aria-label*="assistant"] { border-left: 5px solid #3a7bd5; }
    .stChatInput > div > div > div { background-color: rgba(255, 255, 255, 0.1) !important; border: 1px solid rgba(255, 255, 255, 0.3) !important; border-radius: 25px !important; }
    .stChatInput input { color: white !important; }
    section[data-testid="stSidebar"] { background-color: rgba(15, 12, 41, 0.95); border-right: 1px solid rgba(255,255,255,0.1); }
    .stButton button { background: linear-gradient(90deg, #00d2ff, #3a7bd5); color: white; border: none; border-radius: 20px; font-weight: bold; padding: 10px 24px; }
    .status-box { background-color: rgba(0, 210, 255, 0.1); padding: 10px; border-radius: 10px; border-left: 3px solid #00d2ff; margin: 10px 0; font-size: 0.9rem; color: #e0e0e0; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION (API Keys) ---
GROQ_KEY = "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"
GEMINI_KEY = "AIzaSyD0mlq3W9veyvc-9piMFgAypx8KCjdLc4w"

# --- SAFE INITIALIZATION ---
@st.cache_resource
def init_models():
    g_client = None
    g_model = None
    
    # 1. Groq Setup
    try:
        g_client = Groq(api_key=GROQ_KEY)
    except: pass

    # 2. Gemini Setup (Using 'gemini-pro' for Maximum Stability)
    try:
        genai.configure(api_key=GEMINI_KEY)
        # 'gemini-pro' is the most stable model for free tier
        g_model = genai.GenerativeModel('gemini-pro') 
    except: pass
        
    return g_client, g_model

groq_client, gemini_model = init_models()

# --- MEMORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- TOOL: INTERNET SEARCH ---
def search_tool(query):
    try:
        with DDGS() as ddgs:
            return "\n".join([r['body'] for r in ddgs.text(query, max_results=3)])
    except:
        return "No internet data."

# --- MAIN BRAIN ---
def generate_response(user_prompt):
    # Step 1: Check if search needed
    keywords = ["news", "live", "weather", "market", "price", "today", "aaj", "latest"]
    use_net = any(k in user_prompt.lower() for k in keywords)
    
    context = ""
    if use_net:
        with st.spinner("🌐 Internet Search Active..."):
            context = search_tool(user_prompt)

    full_prompt = user_prompt
    if context:
        full_prompt = f"Answer based on this live data:\n{context}\n\nQuestion: {user_prompt}"

    history = [{"role": "system", "content": "You are JARVIS."}] + st.session_state.messages + [{"role": "user", "content": full_prompt}]

    # ATTEMPT 1: GROQ (Primary - Fast)
    if groq_client:
        try:
            res = groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=history
            )
            return res.choices[0].message.content, "🚀 Groq Llama 3"
        except:
            pass # Silently fail to backup

    # ATTEMPT 2: GEMINI (Backup - Stable)
    if gemini_model:
        try:
            # Gemini simple generate
            res = gemini_model.generate_content(full_prompt)
            return res.text, "💡 Gemini Pro"
        except Exception as e:
            # If even Gemini fails
            return f"Backup Error: {str(e)}", "❌ Error"

    return "System Offline.", "❌ Offline"

# --- SIDEBAR UI ---
with st.sidebar:
    st.markdown("<h2>⚡ Control Panel</h2>", unsafe_allow_html=True)
    if st.button("🗑️ Clear Memory", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("### 🧠 Status")
    st.metric("Groq Engine", "🟢 Ready" if groq_client else "🔴 Down")
    st.metric("Gemini Core", "🟢 Ready" if gemini_model else "🔴 Down")
    st.markdown("---")
    st.info("Ye AI khud decide karta hai kaunsa model use karna hai.")

# --- MAIN CHAT UI ---
st.markdown('<h1 class="main-title">J.A.R.V.I.S</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; opacity: 0.7;">Powered by Groq & Gemini</p>', unsafe_allow_html=True)

# Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
if prompt := st.chat_input("Ask anything..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            ans, model = generate_response(prompt)
            
            st.markdown(f"<div class='status-box'>Powered by: <b>{model}</b></div>", unsafe_allow_html=True)
            
            # Typewriter Effect
            placeholder = st.empty()
            text = ""
            for w in ans.split():
                text += w + " "
                time.sleep(0.015)
                placeholder.markdown(text + "▌")
            placeholder.markdown(text)
            
            st.session_state.messages.append({"role": "assistant", "content": ans})