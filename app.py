import streamlit as st
from groq import Groq
import google.generativeai as genai
from duckduckgo_search import DDGS
import time
import random

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="JARVIS AI", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS (THE MAGIC STYLING) ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: #ffffff;
    }
    
    /* Title Styling */
    .main-title {
        font-size: 3rem !important;
        font-weight: 800;
        background: linear-gradient(90deg, #00d2ff, #3a7bd5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 20px;
    }

    /* Chat Messages Styling */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* User Message */
    [data-testid="stChatMessage"][aria-label*="user"] {
        border-left: 4px solid #00d2ff;
    }

    /* Assistant Message */
    [data-testid="stChatMessage"][aria-label*="assistant"] {
        border-left: 4px solid #3a7bd5;
    }

    /* Input Box */
    .stChatInput > div > div > div {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 25px !important;
    }
    
    .stChatInput input {
        color: white !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: rgba(26, 26, 46, 0.95);
        border-right: 1px solid rgba(255,255,255,0.1);
    }

    /* Buttons */
    .stButton button {
        background: linear-gradient(90deg, #00d2ff, #3a7bd5);
        color: white;
        border: none;
        border-radius: 20px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(0, 210, 255, 0.5);
    }

    /* Status Indicator */
    .status-box {
        background-color: rgba(0, 0, 0, 0.3);
        padding: 10px;
        border-radius: 10px;
        border-left: 3px solid #00d2ff;
        margin: 10px 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION & SECRETS ---
# Deployment ke liye Streamlit Cloud mein Secrets mein save karna hoga
# Abhi ke liye direct daal rahe hain testing ke liye
GROQ_KEY = "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"
GEMINI_KEY = "AIzaSyD0mlq3W9veyvc-9piMFgAypx8KCjdLc4w"

# --- CLIENT INITIALIZATION (Lazy Loading) ---
@st.cache_resource
def init_clients():
    groq_c = None
    gemini_m = None
    
    try:
        groq_c = Groq(api_key=GROQ_KEY)
    except: pass
    
    try:
        genai.configure(api_key=GEMINI_KEY)
        gemini_m = genai.GenerativeModel('gemini-1.5-flash-latest')
    except: pass
    
    return groq_c, gemini_m

groq_client, gemini_model = init_clients()

# --- MEMORY MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- TOOLS ---
def search_internet_tool(query):
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=4)]
        context = "\n\n".join([f"Source: {r['title']}\n{r['body']}" for r in results])
        return context
    except:
        return "Could not fetch live data."

# --- MAIN BRAIN LOGIC ---
def get_response(user_prompt):
    # 1. Check Internet Need
    search_keywords = ["news", "latest", "live", "weather", "market", "price", "score", "aaj"]
    need_search = any(word in user_prompt.lower() for word in search_keywords)
    
    context_data = ""
    if need_search:
        with st.spinner("🌐 Scanning the Web..."):
            context_data = search_internet_tool(user_prompt)
    
    # Prompt Engineering
    system_prompt = "You are JARVIS, an advanced AI assistant. Be concise, helpful, and powerful."
    final_prompt = user_prompt
    
    if context_data:
        final_prompt = f"""
        User Question: {user_prompt}
        
        [LIVE SEARCH DATA]:
        {context_data}
        
        Instructions: Use the live data above to answer the user's question accurately. If the data is irrelevant, ignore it.
        """

    messages_hist = [{"role": "system", "content": system_prompt}] + st.session_state.messages + [{"role": "user", "content": final_prompt}]

    # 2. ATTEMPT GROQ (FAST LANE)
    if groq_client:
        try:
            res = groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=messages_hist,
                temperature=0.7
            )
            return res.choices[0].message.content, "🚀 Groq Llama 3 (Fast)", True
        except Exception as e:
            # Fail silently and move to backup
            pass

    # 3. ATTEMPT GEMINI (BACKUP LANE)
    if gemini_model:
        try:
            # Gemini doesn't support system prompt in simple generate_content easily without chat session
            # So we combine history manually for simplicity in this deployment
            formatted_history = ""
            for m in st.session_state.messages:
                formatted_history += f"{m['role']}: {m['content']}\n"
            
            full_text = f"{system_prompt}\n\nHistory:\n{formatted_history}\nUser: {final_prompt}"
            
            res = gemini_model.generate_content(full_text)
            return res.text, "💡 Gemini 1.5 (Smart)", True
        except Exception as e:
            return f"Critical Error: Both AI systems offline. {str(e)}", "❌ Offline", False

    return "No AI Clients Available.", "❌ Error", False

# --- SIDEBAR UI ---
with st.sidebar:
    st.markdown("<h2>⚡ Control Panel</h2>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🗑️ Clear Memory", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("### 🧠 AI Status")
    st.metric("Groq (Fast)", "Online" if groq_client else "Offline")
    st.metric("Gemini (Smart)", "Online" if gemini_model else "Offline")
    
    st.markdown("---")
    st.markdown("<p style='opacity: 0.5; font-size: 0.8rem;'>JARVIS v2.0<br>Powered by Llama 3 & Gemini</p>", unsafe_allow_html=True)

# --- MAIN CHAT UI ---
st.markdown('<h1 class="main-title">J.A.R.V.I.S</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; opacity: 0.8;">Just A Rather Very Intelligent System</p>', unsafe_allow_html=True)

# Chat History Display
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input Handling
if prompt := st.chat_input("Ask JARVIS anything..."):
    # User Message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # AI Response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response, model_used, success = get_response(prompt)
            
            # Display Model Info
            st.markdown(f"<div class='status-box'>Active Model: <b>{model_used}</b></div>", unsafe_allow_html=True)
            
            # Typewriter Effect
            message_placeholder = st.empty()
            full_response = ""
            
            # Simple chunk simulation for visual effect
            chunks = response.split(" ")
            for i, word in enumerate(chunks):
                full_response += word + " "
                time.sleep(0.01) # Tiny delay for effect
                message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
            # Save to memory
            st.session_state.messages.append({"role": "assistant", "content": response})