import os
import json
import re

# ⚠️ СЛОЖИ СИ КЛЮЧА ТУК ⚠️
OPENAI_API_KEY = "your openai api key here"

# --- НАСТРОЙКА ---
TARGET_SAMPLE_RATE = 48000
SILENCE_THRESHOLD = 0.05
SILENCE_DURATION = 1.7
MAX_RECORD_TIME = 25.0

APP_DATA_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), "TranslatyPro")
os.makedirs(APP_DATA_DIR, exist_ok=True)
SETTINGS_FILE = os.path.join(APP_DATA_DIR, "translaty_settings.json")

# --- СКРИТИ ИНСТРУКЦИИ ЗА ИЗКУСТВЕНИЯ ИНТЕЛЕКТ ---
AI_INSTRUCTIONS = "Translate accurately and naturally. Fix any voice recognition errors If you see words which are in the phrase but could have been misheard replace them correctly by using the context."

IGNORED_PHRASES = [
    "Amara.org", "Untertitel", "Subtitles", "MBC", "Copyright", "Субтитри",
    "Thank you for watching", "Thanks for watching", "гледате видеото",
    "гледахте това", "Благодаря ви", "абонирайте", "subscribe"
]

# --- СПИСЪК С ЕЗИЦИ ---
LANGUAGES = {
    "Bulgarian": "bg", "English": "en", "German": "de", "Afrikaans": "af",
    "Arabic": "ar", "Chinese (Mandarin)": "zh", "Croatian": "hr", "Czech": "cs",
    "Danish": "da", "Dutch": "nl", "Finnish": "fi", "French": "fr",
    "Greek": "el", "Hebrew": "he", "Hindi": "hi", "Hungarian": "hu",
    "Indonesian": "id", "Italian": "it", "Japanese": "ja", "Korean": "ko",
    "Norwegian": "no", "Polish": "pl", "Portuguese": "pt", "Romanian": "ro",
    "Russian": "ru", "Slovak": "sk", "Spanish": "es", "Swedish": "sv",
    "Thai": "th", "Turkish": "tr", "Ukrainian": "uk", "Vietnamese": "vi"
}
ALL_LANG_NAMES = sorted(list(LANGUAGES.keys()))

OPENAI_VOICES = [
    "Nova (Female)",
    "Shimmer (Female)",
    "Echo (Male)",
    "Onyx (Deep Male)",
    "Fable (Male)",
    "Alloy (Neutral)"
]

# --- РЕЧНИК С ПРЕВОДИ ЗА САМИЯ ИНТЕРФЕЙС ---
UI_TEXT = {
    "English": {
        "title": "🌍 Translaty Pro",
        "tab_out": "📤 Outgoing",
        "tab_in": "📥 Incoming",
        "tab_set": "⚙️ Settings",
        "tab_faq": "📖 FAQ",
        "i_speak": "I speak in:",
        "translates_to": "⬇️ Translates to ⬇️",
        "they_speak": "They speak in:",
        "btn_start_trans": "▶ START TRANSLATION",
        "btn_start_listen": "▶ START LISTENING",
        "btn_stop": "🛑 STOP",
        "lbl_mic": "Microphone (Input):",
        "lbl_cab_in": "To App (CABLE-A):",
        "lbl_cab_out": "From App (CABLE-B):",
        "lbl_ph": "Headphones (Output):",
        "lbl_theme": "Dark Theme",
        "lbl_ui_lang": "Interface Language:",
        "lbl_voice_out": "AI Voice (To Them):",
        "lbl_voice_in": "AI Voice (To Me):",
        "msg_restart": "Please restart the application to apply the new language.",
        "msg_error": "Error",
        "msg_no_devices": "Please go to 'Settings' and select audio devices!",
        "faq_content": "📌 HOW TO SET UP:\n\n1. Voice App (Discord, Teams, Meet):\n• Microphone: 'CABLE-A Output'\n• Speakers: 'CABLE-B Input'\n\n2. In this app (Settings):\n• Microphone: Your real mic\n• To App: 'CABLE-A Input'\n• From App: 'CABLE-B Output'\n• Headphones: Your real headphones"
    },
    "Bulgarian": {
        "title": "🌍 Translaty Pro",
        "tab_out": "📤 Изходящ",
        "tab_in": "📥 Входящ",
        "tab_set": "⚙️ Настройки",
        "tab_faq": "📖 FAQ",
        "i_speak": "Аз говоря на:",
        "translates_to": "⬇️ Превежда се на ⬇️",
        "they_speak": "Отсреща говорят на:",
        "btn_start_trans": "▶ СТАРТ ПРЕВОД",
        "btn_start_listen": "▶ СТАРТ СЛУШАНЕ",
        "btn_stop": "🛑 СПРИ",
        "lbl_mic": "Микрофон (Вход):",
        "lbl_cab_in": "Към Приложение (CABLE-A):",
        "lbl_cab_out": "От Приложение (CABLE-B):",
        "lbl_ph": "Слушалки (Изход):",
        "lbl_theme": "Тъмна тема",
        "lbl_ui_lang": "Език на интерфейса:",
        "lbl_voice_out": "AI Глас (Към тях):",
        "lbl_voice_in": "AI Глас (Към мен):",
        "msg_restart": "Моля, рестартирайте приложението, за да се приложи езикът.",
        "msg_error": "Грешка",
        "msg_no_devices": "Отидете в 'Настройки' и изберете аудио устройства!",
        "faq_content": "📌 КАК ДА НАСТРОИТЕ:\n\n1. Във вашето приложение (Discord, Meet):\n• Микрофон: 'CABLE-A Output'\n• Високоговорители: 'CABLE-B Input'\n\n2. В тази програма:\n• Микрофон: Вашият реален микрофон\n• Към Приложение: 'CABLE-A Input'\n• От Приложение: 'CABLE-B Output'\n• Слушалки: Вашите реални слушалки"
    },
    "German": {
        "title": "🌍 Translaty Pro",
        "tab_out": "📤 Ausgehend",
        "tab_in": "📥 Eingehend",
        "tab_set": "⚙️ Einstellungen",
        "tab_faq": "📖 FAQ",
        "i_speak": "Ich spreche auf:",
        "translates_to": "⬇️ Übersetzt in ⬇️",
        "they_speak": "Gegenüber spricht auf:",
        "btn_start_trans": "▶ ÜBERSETZUNG STARTEN",
        "btn_start_listen": "▶ ZUHÖREN STARTEN",
        "btn_stop": "🛑 STOPP",
        "lbl_mic": "Mikrofon (Eingang):",
        "lbl_cab_in": "Zur App (CABLE-A):",
        "lbl_cab_out": "Von App (CABLE-B):",
        "lbl_ph": "Kopfhörer (Ausgang):",
        "lbl_theme": "Dunkles Design",
        "lbl_ui_lang": "Sprache:",
        "lbl_voice_out": "KI-Stimme (Zu ihnen):",
        "lbl_voice_in": "KI-Stimme (Zu mir):",
        "msg_restart": "Bitte starten Sie die App neu, um die neue Sprache anzuwenden.",
        "msg_error": "Fehler",
        "msg_no_devices": "Bitte gehen Sie zu 'Einstellungen' und wählen Sie Audiogeräte aus!",
        "faq_content": "📌 SO RICHTEN SIE DIE APP EIN:\n\n1. In Ihrer App (Discord, Teams, etc.):\n• Mikrofon: 'CABLE-A Output'\n• Lautsprecher: 'CABLE-B Input'\n\n2. In dieser App:\n• Mikrofon: Ihr echtes Mikrofon\n• Zur App: 'CABLE-A Input'\n• Von App: 'CABLE-B Output'\n• Kopfhörer: Ihre echten Kopfhörer"
    }
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return (
                    data.get("ui_language", "English"),
                    data.get("voice_out", "Onyx (Deep Male)"),
                    data.get("voice_in", "Nova (Female)")
                )
        except:
            pass
    return "English", "Onyx (Deep Male)", "Nova (Female)"

def save_settings(lang, voice_out, voice_in):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "ui_language": lang,
            "voice_out": voice_out,
            "voice_in": voice_in
        }, f)

def check_key_safety(key):
    return not bool(re.search('[а-яА-Я]', key))
