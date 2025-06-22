import streamlit as st
import openai
import json
import os

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

# --- Функции для работы с конфигурацией ---

def load_config():
    """Загружает конфигурацию из JSON файла."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                # Добавляем проверку на пустой файл
                content = f.read()
                if not content:
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            st.error(f"Ошибка чтения файла конфигурации {CONFIG_FILE}. Файл будет перезаписан при сохранении.")
            return {} # Возвращаем пустой словарь при ошибке
        except Exception as e:
            st.error(f"Неожиданная ошибка при загрузке конфигурации: {e}")
            return {}
    return {}

def save_config(config):
    """Сохраняет конфигурацию в JSON файл."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        st.error(f"Не удалось сохранить конфигурацию: {e}")

# --- Инициализация приложения ---

st.set_page_config(page_title="OpenRouter Chat", layout="wide")
st.title("💬 Локальный Чат с OpenRouter")
st.caption("Интерфейс для взаимодействия с моделями через API OpenRouter.ai")

# Загрузка конфигурации
config = load_config()

# Инициализация состояния чата и настроек
if "messages" not in st.session_state:
    st.session_state.messages = []

# Определяем модель по умолчанию: сначала из конфига, потом первую из списка
default_model = config.get("last_selected_model", DEFAULT_MODELS[0] if DEFAULT_MODELS else "")
if default_model not in DEFAULT_MODELS and DEFAULT_MODELS: # Если сохраненной нет в текущем списке
    default_model = DEFAULT_MODELS[0]
elif not DEFAULT_MODELS: # Если список моделей пуст
     default_model = ""

if "selected_model" not in st.session_state:
    st.session_state.selected_model = default_model
if "api_key" not in st.session_state:
    st.session_state.api_key = config.get("api_key", "")
if "site_url" not in st.session_state:
     st.session_state.site_url = config.get("site_url", "")
if "site_name" not in st.session_state:
     st.session_state.site_name = config.get("site_name", "")

# --- Боковая панель для настроек ---
with st.sidebar:
    st.header("⚙️ Настройки OpenRouter")

    # Ввод API ключа
    api_key_input = st.text_input(
        "OpenRouter API Key",
        type="password",
        value=st.session_state.api_key,
        key="api_key_input_widget", # Уникальный ключ для виджета
        help="Введите ваш API ключ с OpenRouter.ai. Ключ сохраняется локально в `openrouter_config.json`."
    )
    # Сохраняем ключ, если он изменился
    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
        config["api_key"] = api_key_input
        save_config(config)
        # Не используем rerun(), чтобы не прерывать ввод

    # Выбор модели
    if DEFAULT_MODELS: # Показываем выбор, только если список не пуст
        # Устанавливаем индекс по умолчанию, если сохраненная модель есть в списке
        try:
            # Используем текущее значение из session_state для индекса
            current_model_in_state = st.session_state.selected_model
            if current_model_in_state in DEFAULT_MODELS:
                 default_model_index = DEFAULT_MODELS.index(current_model_in_state)
            else:
                 default_model_index = 0 # Если текущей модели нет в списке, берем первую
        except ValueError:
            default_model_index = 0

        selected_model_input = st.selectbox(
            "Выберите модель",
            options=DEFAULT_MODELS,
            index=default_model_index,
            key="model_select_widget", # Уникальный ключ для виджета
            help="Выберите модель для общения. Список моделей на OpenRouter: https://openrouter.ai/models"
        )
        # Сохраняем модель, если она изменилась
        if selected_model_input != st.session_state.selected_model:
            st.session_state.selected_model = selected_model_input
            config["last_selected_model"] = selected_model_input
            save_config(config)
            # Не используем rerun(), смена применится при след. запросе
    else:
        st.warning("Список моделей пуст. Пожалуйста, добавьте модели в DEFAULT_MODELS в коде.")
        st.session_state.selected_model = "" # Сбрасываем выбранную модель

    st.divider()

    # Необязательные заголовки
    st.subheader("Необязательные Заголовки (для рейтинга)")
    site_url_input = st.text_input(
        "Your Site URL (HTTP-Referer)",
        value=st.session_state.site_url,
        key="site_url_input_widget",
        help="Опционально. URL вашего сайта/приложения."
    )
    if site_url_input != st.session_state.site_url:
        st.session_state.site_url = site_url_input
        config["site_url"] = site_url_input
        save_config(config)

    site_name_input = st.text_input(
        "Your Site Name (X-Title)",
        value=st.session_state.site_name,
        key="site_name_input_widget",
        help="Опционально. Название вашего сайта/приложения."
    )
    if site_name_input != st.session_state.site_name:
        st.session_state.site_name = site_name_input
        config["site_name"] = site_name_input
        save_config(config)

    st.divider()

    # Кнопка очистки чата
    if st.button("🗑️ Очистить историю чата"):
        st.session_state.messages = []
        st.rerun() # Перезагружаем страницу, чтобы очистить чат

    st.caption(f"Настройки сохраняются в: {os.path.abspath(CONFIG_FILE)}")
    st.caption("⚠️ Ключ API хранится в файле локально. Не передавайте этот файл другим.")

# --- Основная область чата ---

# Отображение сообщений чата из истории
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Поле ввода пользователя
if prompt := st.chat_input("Ваше сообщение..."):
    # Проверка наличия API ключа и выбранной модели
    if not st.session_state.api_key:
        st.warning("Пожалуйста, введите ваш OpenRouter API Key в настройках (боковая панель).")
        st.stop()
    if not st.session_state.selected_model:
         st.warning("Пожалуйста, выберите модель в настройках (боковая панель).")
         st.stop()

    # Добавить сообщение пользователя в историю и отобразить
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Отобразить сообщение ассистента и отправить запрос
    with st.chat_message("assistant"):
        message_placeholder = st.empty() # Заполнитель для ответа
        full_response = "" # Переменная для хранения полного ответа или ошибки
        try:
            # Инициализация клиента OpenAI для OpenRouter
            client = openai.OpenAI(
                base_url=OPENROUTER_BASE_URL,
                api_key=st.session_state.api_key,
                # Можно добавить таймауты, если запросы долгие
                # timeout=30.0,
                # max_retries=2,
            )

            # Формирование необязательных заголовков
            extra_headers = {}
            if st.session_state.site_url:
                 extra_headers["HTTP-Referer"] = st.session_state.site_url
            if st.session_state.site_name:
                 extra_headers["X-Title"] = st.session_state.site_name

            # Отправка запроса с текущей историей сообщений
            completion = client.chat.completions.create(
                model=st.session_state.selected_model,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages # Берем всю историю
                ],
                extra_headers=extra_headers if extra_headers else None,
                extra_body={}, # Как в документации OpenRouter
                # stream=False # Пока не используем стриминг для простоты
            )

            # --- НАДЕЖНАЯ ПРОВЕРКА ОТВЕТА ---
            if completion and completion.choices and len(completion.choices) > 0:
                first_choice = completion.choices[0]
                # Проверяем наличие message и content внутри него
                if hasattr(first_choice, 'message') and first_choice.message and hasattr(first_choice.message, 'content') and first_choice.message.content is not None:
                    # Все в порядке, извлекаем ответ
                    full_response = first_choice.message.content
                    message_placeholder.markdown(full_response) # Отображаем ответ
                else:
                    # Структура ответа некорректна (отсутствует message или content)
                    error_message = "Ошибка: API вернул ответ, но структура сообщения некорректна."
                    # Пытаемся получить хоть какой-то текст из ответа для диагностики
                    finish_reason = getattr(first_choice, 'finish_reason', 'N/A')
                    error_detail = f"Finish reason: {finish_reason}. Message object: {getattr(first_choice, 'message', 'N/A')}"
                    st.error(f"{error_message} {error_detail}")
                    st.warning(f"Полный ответ API (choice[0]): {first_choice}") # Показываем часть ответа
                    full_response = f"Ошибка: {error_message}"
                    message_placeholder.error(full_response) # Отображаем ошибку в чате
            else:
                # Список 'choices' пуст или отсутствует в ответе
                error_message = "Ошибка: API не вернул ожидаемый результат (ответ пуст или некорректен)."
                st.error(error_message)
                st.warning(f"Полный ответ API: {completion}") # Показываем весь ответ
                full_response = f"Ошибка: {error_message}"
                message_placeholder.error(full_response) # Отображаем ошибку в чате

        # --- БЛОКИ ОБРАБОТКИ ОШИБОК API ---
        except openai.AuthenticationError:
            error_message = "Ошибка аутентификации (401). Проверьте правильность вашего API ключа OpenRouter."
            message_placeholder.error(error_message)
            full_response = f"Ошибка: {error_message}"
        except openai.PermissionDeniedError: # Часто бывает при нехватке кредитов
             error_message = "Ошибка доступа (403). Возможно, у вас недостаточно кредитов или нет прав на использование этой модели."
             message_placeholder.error(error_message)
             full_response = f"Ошибка: {error_message}"
        except openai.NotFoundError:
            error_message = f"Ошибка: Модель '{st.session_state.selected_model}' не найдена (404) на OpenRouter или недоступна."
            message_placeholder.error(error_message)
            full_response = f"Ошибка: {error_message}"
        except openai.RateLimitError:
             error_message = "Ошибка: Превышен лимит запросов (429) на OpenRouter. Попробуйте позже или проверьте лимиты вашего аккаунта."
             message_placeholder.error(error_message)
             full_response = f"Ошибка: {error_message}"
        except openai.APIConnectionError as e:
            error_message = f"Ошибка подключения к OpenRouter: {e}. Проверьте ваше интернет-соединение и доступность API."
            message_placeholder.error(error_message)
            full_response = f"Ошибка: {error_message}"
        except openai.APIStatusError as e: # Ловим другие ошибки HTTP (5xx, 4xx)
            error_message = f"Ошибка API OpenRouter (HTTP {e.status_code}): {e.message}"
            st.error(f"Полный ответ ошибки API: {e.response.text}") # Показываем тело ответа
            message_placeholder.error(error_message)
            full_response = f"Ошибка: {error_message}"
        except openai.APIError as e: # Общая ошибка OpenAI/OpenRouter
            error_message = f"Произошла общая ошибка API OpenRouter: {e}"
            message_placeholder.error(error_message)
            full_response = f"Ошибка: {error_message}"
        except Exception as e:
            # --- ЛОВИМ ВСЕ ОСТАЛЬНЫЕ ОШИБКИ ---
            error_type = type(e).__name__
            error_message = f"Произошла непредвиденная ошибка: {error_type}: {e}"
            st.error(error_message)
            st.error("Traceback:")
            # Выводим полный traceback в консоль и в приложение для легкой отладки
            traceback_str = traceback.format_exc()
            print(traceback_str) # В консоль сервера Streamlit
            st.code(traceback_str) # В интерфейс приложения
            full_response = f"Ошибка: {error_message}"
            message_placeholder.error(f"{full_response}\n(Подробности см. в логах или выше)") # Отображаем краткую ошибку в чате

    # Добавить финальный ответ ассистента (или сообщение об ошибке) в историю
    st.session_state.messages.append({"role": "assistant", "content": full_response})
