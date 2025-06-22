import streamlit as st
import openai
import json
import os
import time

# --- Инициализация приложения ---
st.set_page_config(
    page_title="Neural Nexus",
    layout="wide",
    initial_sidebar_state="expanded"
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
    /* Скрываем верхнюю панель */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #0a0a1f 0%, #1a1a3f 100%);
        color: #e0e0ff;
    }
    
    .main-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 3.5em !important;
        text-align: center;
        text-transform: uppercase;
        background: linear-gradient(120deg, #00ffff, #ff00ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1em !important;
        letter-spacing: 3px;
        text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
        animation: neonPulse 2s infinite;
    }
    
    .stChatMessage {
        background: rgba(26, 26, 46, 0.8) !important;
        border-radius: 15px !important;
        padding: 1.5em !important;
        margin: 1em 0 !important;
        border: 1px solid rgba(0, 255, 255, 0.2) !important;
        box-shadow: 0 4px 15px rgba(0, 255, 255, 0.1) !important;
        animation: messageAppear 0.5s ease forwards;
    }
    
    .stChatMessage::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, var(--glow-color, #00ffff), transparent);
        animation: scanline 2s linear infinite;
    }
    
    .stChatMessage[data-testid="user-message"] {
        background: rgba(0, 255, 255, 0.1) !important;
        border-color: rgba(0, 255, 255, 0.3) !important;
        margin-left: 2em !important;
        animation-delay: calc(var(--index, 0) * 0.8s);
    }
    
    .stChatMessage[data-testid="assistant-message"] {
        background: rgba(255, 0, 255, 0.1) !important;
        border-color: rgba(255, 0, 255, 0.3) !important;
        margin-right: 2em !important;
        animation-delay: calc(var(--index, 0) * 0.8s);
    }
    
    .stChatInputContainer {
        animation: rgbBorder 10s linear infinite !important;
        border-width: 2px !important;
        background: rgba(13, 13, 37, 0.7) !important;
        backdrop-filter: blur(10px);
        padding: 10px !important;
        margin: 0 auto !important;
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 1000 !important;
    }
    
    .stChatInputContainer > div {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    .stChatInputContainer textarea {
        min-height: 40px !important;
        padding: 8px 12px !important;
        background: rgba(13, 13, 37, 0.7) !important;
        color: rgb(200, 200, 255) !important;
        border-radius: 10px !important;
        margin: 0 !important;
    }
    
    .stChatInputContainer button {
        background: linear-gradient(90deg, #00ffff, #ff00ff) !important;
        color: #0a0a1f !important;
        border: none !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        transition: all 0.3s ease !important;
        position: relative;
        overflow: hidden;
    }
    
    .stChatInputContainer button:hover {
        transform: translateY(-2px) scale(1.05) !important;
        box-shadow: 0 5px 20px rgba(0, 255, 255, 0.4) !important;
    }
    
    .stChatInputContainer button::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        transform: rotate(45deg);
        animation: buttonGlow 2s linear infinite;
    }
    
    @keyframes buttonGlow {
        0% { transform: rotate(45deg) translateX(-100%); }
        100% { transform: rotate(45deg) translateX(100%); }
    }
    
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Orbitron', sans-serif;
        font-weight: bold;
        font-size: 1.2em;
        margin-right: 1em;
        color: #0a0a1f;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .avatar:hover {
        transform: scale(1.1) rotate(5deg);
    }
    
    .avatar::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        transform: rotate(45deg);
        animation: avatarGlow 2s linear infinite;
    }
    
    @keyframes avatarGlow {
        0% { transform: rotate(45deg) translateX(-100%); }
        100% { transform: rotate(45deg) translateX(100%); }
    }
    
    .connection-status {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 10px 20px;
        background: rgba(26, 26, 46, 0.8);
        border-radius: 10px;
        border: 1px solid #00ffff;
        color: #00ffff;
        font-family: 'Orbitron', sans-serif;
        font-size: 0.8em;
    }
    
    /* Анимации */
    @keyframes neonPulse {
        0% { opacity: 1; }
        50% { opacity: 0.8; }
        100% { opacity: 1; }
    }
    
    @keyframes messageAppear {
        0% {
            opacity: 0;
            transform: translateY(20px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes scanline {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    @keyframes glow {
        0% { box-shadow: 0 0 5px rgba(0, 255, 255, 0.2); }
        50% { box-shadow: 0 0 20px rgba(0, 255, 255, 0.4); }
        100% { box-shadow: 0 0 5px rgba(0, 255, 255, 0.2); }
    }
    
    /* Применение анимаций */
    .stChatMessage {
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    .stChatMessage:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 255, 255, 0.2) !important;
    }
    
    /* Эффект печати */
    .typing-effect {
        border-right: 2px solid var(--glow-color, #00ffff);
        animation: blink 1s step-end infinite;
        white-space: pre-wrap;
    }
    
    @keyframes blink {
        0%, 100% { border-color: transparent; }
        50% { border-color: var(--glow-color, #00ffff); }
    }

    /* Базовые стили для всех сообщений */
    .stChatMessage {
        opacity: 0;
        animation: messageAppear 0.5s ease forwards;
        animation-play-state: paused;
    }

    /* Мгновенное появление первого сообщения */
    .stChatMessage:first-of-type {
        opacity: 1 !important;
        animation: none !important;
    }

    /* Анимация появления */
    @keyframes messageAppear {
        0% {
            opacity: 0;
            transform: translateY(20px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Стили для сообщений пользователя */
    [data-testid="user-message"] {
        background: rgba(0, 255, 255, 0.1) !important;
        border-color: rgba(0, 255, 255, 0.3) !important;
        margin-left: 2em !important;
        animation-delay: calc(var(--index, 0) * 0.8s);
        animation-play-state: running;
    }

    /* Стили для сообщений ассистента */
    [data-testid="assistant-message"] {
        background: rgba(255, 0, 255, 0.1) !important;
        border-color: rgba(255, 0, 255, 0.3) !important;
        margin-right: 2em !important;
        animation-delay: calc(var(--index, 0) * 0.8s);
        animation-play-state: running;
    }

    /* Hover эффекты */
    .stChatMessage:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0, 255, 255, 0.2) !important;
        transition: all 0.3s ease;
    }

    /* Динамические задержки для анимации */
    .stChatMessage:nth-child(1) { --index: 0; animation-play-state: running; }
    .stChatMessage:nth-child(2) { --index: 1; animation-play-state: running; }
    .stChatMessage:nth-child(3) { --index: 2; animation-play-state: running; }
    .stChatMessage:nth-child(4) { --index: 3; animation-play-state: running; }
    .stChatMessage:nth-child(5) { --index: 4; animation-play-state: running; }
    .stChatMessage:nth-child(n+6) { --index: 5; animation-play-state: running; }

    /* Сброс анимации при добавлении новых сообщений */
    .stChatMessage:not(:first-of-type) {
        animation: none;
        animation: messageAppear 0.5s ease forwards;
        animation-play-state: running;
    }

    /* RGB анимации */
    @keyframes rgbBorder {
        0% { border-color: rgba(255, 0, 0, 0.3); box-shadow: 0 0 15px rgba(255, 0, 0, 0.2); }
        33% { border-color: rgba(0, 255, 0, 0.3); box-shadow: 0 0 15px rgba(0, 255, 0, 0.2); }
        66% { border-color: rgba(0, 0, 255, 0.3); box-shadow: 0 0 15px rgba(0, 0, 255, 0.2); }
        100% { border-color: rgba(255, 0, 0, 0.3); box-shadow: 0 0 15px rgba(255, 0, 0, 0.2); }
    }

    @keyframes rgbText {
        0% { color: rgb(255, 0, 255); }
        25% { color: rgb(255, 0, 0); }
        50% { color: rgb(0, 255, 255); }
        75% { color: rgb(0, 255, 0); }
        100% { color: rgb(255, 0, 255); }
    }

    @keyframes rgbGlow {
        0% { text-shadow: 0 0 10px rgba(255, 0, 255, 0.7); }
        25% { text-shadow: 0 0 10px rgba(255, 0, 0, 0.7); }
        50% { text-shadow: 0 0 10px rgba(0, 255, 255, 0.7); }
        75% { text-shadow: 0 0 10px rgba(0, 255, 0, 0.7); }
        100% { text-shadow: 0 0 10px rgba(255, 0, 255, 0.7); }
    }

    /* Применяем RGB-эффекты */
    .main-title {
        animation: rgbText 10s linear infinite, rgbGlow 10s linear infinite !important;
    }

    .stChatInputContainer {
        animation: rgbBorder 10s linear infinite !important;
        border-width: 2px !important;
        background: rgba(13, 13, 37, 0.7) !important;
        backdrop-filter: blur(10px);
    }

    button {
        background: rgba(13, 13, 37, 0.7) !important;
        border: 2px solid transparent !important;
        animation: rgbBorder 10s linear infinite !important;
        transition: all 0.3s ease !important;
    }

    button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 15px rgba(255, 0, 255, 0.3) !important;
    }

    .connection-status {
        animation: rgbText 10s linear infinite !important;
        background: rgba(13, 13, 37, 0.7) !important;
        backdrop-filter: blur(10px);
        border: 2px solid transparent;
    }

    /* Добавляем отступ для контента, чтобы он не перекрывался с полем ввода */
    .main .block-container {
        padding-bottom: 80px !important;
    }

    /* Стили для автофокуса */
    textarea[data-testid="stChatInput"] {
        opacity: 1 !important;
        pointer-events: auto !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Заголовок ---
st.markdown("""
<h1 class="main-title">NEURAL NEXUS</h1>
<div style="text-align: center; margin-bottom: 2em;">
    <p style="color: #00ffff; font-size: 1.2em; font-family: 'Orbitron', sans-serif; letter-spacing: 2px;">
        QUANTUM PROCESSING • NEURAL LINK ESTABLISHED
    </p>
</div>
<div class="connection-status">
    ◉ NEURAL LINK ACTIVE
</div>
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
