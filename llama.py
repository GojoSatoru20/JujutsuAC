import streamlit as st
import openai
import json
import os
import time

# --- Инициализация приложения ---
st.set_page_config(
    page_title="Neural Nexus",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Константы и Конфигурация ---
CONFIG_FILE = "openrouter_config.json"
DEFAULT_MODELS = [
    "deepseek/deepseek-r1:free",
    "meta-llama/llama-4-maverick:free",
    "meta-llama/llama-4-scout:free",
    "google/gemini-2.5-pro-exp-03-25:free",
    "google/gemini-2.0-pro-exp-02-05:free",
    "deepseek/deepseek-chat-v3-0324:free",
    "google/gemma-3-27b-it:free",
    "qwen/qwq-32b:free",
    "deepseek/deepseek-r1-0528-qwen3-8b:free",
    # Добавьте сюда другие интересующие модели с OpenRouter
    # Формат: "идентификатор/модели:версия" (если есть)
    # Список моделей: https://openrouter.ai/models
]

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# --- Стили ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700&family=Rajdhani:wght@300;400;500;600&display=swap');
    
    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Global theme */
    .stApp {
        background: linear-gradient(180deg, #0A0B0F 0%, #111729 100%) !important;
        color: #E5E5E5;
        font-family: 'Rajdhani', sans-serif;
        min-height: 100vh;
        position: relative;
    }
    
    /* Glowing background effect */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
            radial-gradient(circle at 20% 20%, rgba(0, 247, 255, 0.05) 0%, transparent 40%),
            radial-gradient(circle at 80% 80%, rgba(29, 78, 216, 0.05) 0%, transparent 40%);
        pointer-events: none;
        z-index: 0;
    }

    /* Main title */
    .main-title {
        font-family: 'Orbitron', sans-serif !important;
        font-size: 4em !important;
        background: linear-gradient(90deg, #00F7FF, #2563EB) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        text-align: center !important;
        margin: 2rem 0 !important;
        letter-spacing: 4px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        position: relative !important;
        z-index: 1 !important;
    }
    
    .main-title::after {
        content: attr(data-text);
        position: absolute;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        z-index: -1;
        filter: blur(15px);
        opacity: 0.5;
        background: linear-gradient(90deg, #00F7FF, #2563EB);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Sidebar */
    .stSidebar {
        background: rgba(17, 23, 41, 0.7) !important;
        backdrop-filter: blur(10px) !important;
        border-right: 1px solid rgba(0, 247, 255, 0.1) !important;
    }

    .stSidebar .block-container {
        padding: 2rem 1rem !important;
    }

    /* System Settings container */
    .stSidebar .element-container {
        background: rgba(17, 23, 41, 0.6) !important;
        border: 1px solid rgba(0, 247, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        margin: 0.5rem 0 !important;
        box-shadow: 
            0 4px 12px rgba(0, 0, 0, 0.3),
            0 0 20px rgba(0, 247, 255, 0.05) !important;
        backdrop-filter: blur(5px) !important;
    }

    /* Sidebar headings */
    .stSidebar h2 {
        font-family: 'Orbitron', sans-serif !important;
        color: #00F7FF !important;
        font-size: 1.2em !important;
        letter-spacing: 2px !important;
        margin-bottom: 1rem !important;
        text-transform: uppercase !important;
    }

    /* Input fields */
    .stTextInput input, .stSelectbox select {
        background: rgba(17, 23, 41, 0.6) !important;
        border: 1px solid rgba(0, 247, 255, 0.2) !important;
        color: #00F7FF !important;
        border-radius: 8px !important;
        font-family: 'Rajdhani', sans-serif !important;
        padding: 0.75rem !important;
        transition: all 0.3s ease !important;
    }

    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: #00F7FF !important;
        box-shadow: 0 0 15px rgba(0, 247, 255, 0.2) !important;
    }

    /* Clear History button */
    .stButton button {
        background: linear-gradient(90deg, #111729, #1E293B) !important;
        border: 1px solid #00F7FF !important;
        color: #00F7FF !important;
        font-family: 'Orbitron', sans-serif !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        padding: 0.75rem !important;
        width: 100% !important;
        margin: 0.5rem 0 !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
        position: relative !important;
        overflow: hidden !important;
    }

    .stButton button:hover {
        background: linear-gradient(90deg, #1E293B, #111729) !important;
        box-shadow: 0 0 20px rgba(0, 247, 255, 0.2) !important;
    }

    .stButton button::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, #00F7FF, #2563EB);
        z-index: -1;
        filter: blur(10px);
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .stButton button:hover::before {
        opacity: 1;
    }

    /* Chat messages */
    .stChatMessage {
        background: rgba(17, 23, 41, 0.6) !important;
        border: 1px solid rgba(0, 247, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        margin: 1rem 2rem !important;
        box-shadow: 
            0 4px 12px rgba(0, 0, 0, 0.3),
            0 0 20px rgba(0, 247, 255, 0.05) !important;
        backdrop-filter: blur(5px) !important;
        transition: all 0.3s ease !important;
    }

    .stChatMessage:hover {
        border-color: rgba(0, 247, 255, 0.3) !important;
        box-shadow: 
            0 4px 12px rgba(0, 0, 0, 0.3),
            0 0 30px rgba(0, 247, 255, 0.1) !important;
    }

    /* Chat input area */
    .stChatInputContainer {
        background: rgba(17, 23, 41, 0.8) !important;
        backdrop-filter: blur(10px) !important;
        border-top: 1px solid rgba(0, 247, 255, 0.1) !important;
        padding: 1.5rem 2rem !important;
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 1000 !important;
    }

    .stChatInputContainer textarea {
        background: rgba(17, 23, 41, 0.6) !important;
        border: 1px solid rgba(0, 247, 255, 0.2) !important;
        color: #E5E5E5 !important;
        border-radius: 40px !important;
        font-family: 'Rajdhani', sans-serif !important;
        padding: 1rem 1.5rem !important;
        min-height: 45px !important;
        max-height: 45px !important;
        font-size: 1rem !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s ease !important;
    }

    .stChatInputContainer textarea:focus {
        border-color: #00F7FF !important;
        box-shadow: 0 0 20px rgba(0, 247, 255, 0.2) !important;
    }

    /* Neural Link Active status */
    .connection-status {
        background: rgba(17, 23, 41, 0.8) !important;
        backdrop-filter: blur(5px) !important;
        border: 1px solid rgba(0, 247, 255, 0.2) !important;
        color: #00F7FF !important;
        font-family: 'Orbitron', sans-serif !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        padding: 0.5rem 1rem !important;
        border-radius: 8px !important;
        position: fixed !important;
        top: 1rem !important;
        right: 1rem !important;
        z-index: 1000 !important;
        animation: pulse 2s infinite !important;
    }

    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(0, 247, 255, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(0, 247, 255, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 247, 255, 0); }
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(17, 23, 41, 0.3);
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(0, 247, 255, 0.2);
        border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(0, 247, 255, 0.4);
    }

    /* Main content area */
    .main .block-container {
        padding-bottom: 120px !important;
    }

    /* Additional elements */
    .stAlert, .stInfo, .stError, .stWarning, .stSuccess {
        background: rgba(17, 23, 41, 0.6) !important;
        backdrop-filter: blur(5px) !important;
        border: 1px solid rgba(0, 247, 255, 0.1) !important;
        color: #E5E5E5 !important;
        border-radius: 8px !important;
    }

    /* Avatar styling */
    .avatar {
        width: 40px !important;
        height: 40px !important;
        border-radius: 8px !important;
        background: rgba(17, 23, 41, 0.8) !important;
        border: 1px solid rgba(0, 247, 255, 0.2) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-family: 'Orbitron', sans-serif !important;
        color: #00F7FF !important;
        font-size: 1.2em !important;
        box-shadow: 0 0 15px rgba(0, 247, 255, 0.1) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Заголовок и статус ---
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 class="main-title" data-text="NEURAL NEXUS">NEURAL NEXUS</h1>
    <p style="color: #00F7FF; font-family: 'Orbitron', sans-serif; letter-spacing: 2px; font-size: 1.2em; margin-top: -1rem;">
        QUANTUM PROCESSING • NEURAL LINK ESTABLISHED
    </p>
</div>
<div class="connection-status">◉ NEURAL LINK ACTIVE</div>
""", unsafe_allow_html=True)

# --- Функции ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                content = f.read()
                return json.loads(content) if content else {}
        except:
            return {}
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        st.error(f"Ошибка сохранения конфигурации: {e}")

# --- Инициализация состояния ---
if "messages" not in st.session_state:
    st.session_state.messages = []

config = load_config()
if "selected_model" not in st.session_state:
    st.session_state.selected_model = config.get("last_selected_model", DEFAULT_MODELS[0])
if "api_key" not in st.session_state:
    st.session_state.api_key = config.get("api_key", "")

# --- Боковая панель ---
with st.sidebar:
    st.markdown("""
    <h2 style="
        color: #00ffff;
        font-family: Orbitron;
        font-size: 1.5em;
        letter-spacing: 2px;
        margin-bottom: 1em;
        text-transform: uppercase;
    ">
        System Settings
    </h2>
    """, unsafe_allow_html=True)
    
    api_key = st.text_input(
        "API KEY",
        type="password",
        value=st.session_state.api_key,
        help="Enter your OpenRouter API key"
    )
    
    selected_model = st.selectbox(
        "AI MODEL",
        options=DEFAULT_MODELS,
        index=DEFAULT_MODELS.index(st.session_state.selected_model) if st.session_state.selected_model in DEFAULT_MODELS else 0,
        format_func=lambda x: x.split('/')[-1].replace('-', ' ').upper()
    )
    
    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()
    
    if api_key != st.session_state.api_key:
        st.session_state.api_key = api_key
        config["api_key"] = api_key
        save_config(config)
    
    if selected_model != st.session_state.selected_model:
        st.session_state.selected_model = selected_model
        config["last_selected_model"] = selected_model
        save_config(config)

# --- Чат ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Инициализация состояния для фокуса
if "focus_set" not in st.session_state:
    st.session_state.focus_set = False

# Добавляем скрипт для автофокуса
st.markdown("""
<script>
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        const textarea = document.querySelector('textarea[data-testid="stChatInput"]');
        if (textarea) {
            textarea.focus();
        }
    }, 100);
});
</script>
""", unsafe_allow_html=True)

# Используем автофокус в поле ввода
if prompt := st.chat_input("Enter message...", key="chat_input", max_chars=None, disabled=False):
    if not st.session_state.api_key:
        st.markdown("""
        <div style="
            padding: 1em;
            border-radius: 10px;
            background: rgba(255, 0, 0, 0.1);
            border: 1px solid rgba(255, 0, 0, 0.3);
            color: #ff0000;
            font-family: 'Orbitron', sans-serif;
            text-align: center;
            margin: 1em 0;
        ">
            Please enter your API key in settings
        </div>
        """, unsafe_allow_html=True)
        st.stop()
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            client = openai.OpenAI(
                base_url=OPENROUTER_BASE_URL,
                api_key=st.session_state.api_key
            )
            
            completion = client.chat.completions.create(
                model=st.session_state.selected_model,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]
            )
            
            full_response = completion.choices[0].message.content
            
            # Эффект печати с увеличенной задержкой
            displayed_response = ""
            for chunk in full_response.split():
                displayed_response += chunk + " "
                time.sleep(0.08)  # Увеличенная задержка для более заметного эффекта печати
                message_placeholder.markdown(f"""
                <div class="typing-effect" style="--glow-color: #ff00ff;">
                    {displayed_response}
                </div>
                """, unsafe_allow_html=True)
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            error_message = f"""
            <div style="
                padding: 1em;
                border-radius: 10px;
                background: rgba(255, 0, 0, 0.1);
                border: 1px solid rgba(255, 0, 0, 0.3);
                color: #ff0000;
                font-family: 'Orbitron', sans-serif;
            ">
                Error: {str(e)}
            </div>
            """
            message_placeholder.markdown(error_message, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": error_message})
