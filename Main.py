import sys
import traceback
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import sounddevice as sd
import numpy as np
import soundfile as sf
from openai import OpenAI
import threading
import queue
import os
import tempfile
import time
import warnings
import scipy.signal
import re
import pystray
from PIL import Image, ImageDraw
import darkdetect
import json

warnings.filterwarnings("ignore")

# --- ЩИТ СРЕЩУ ТИХИ КРАШОВЕ В .EXE (--noconsole) ---
class NullWriter:
    def write(self, text): pass
    def flush(self): pass

if sys.stdout is None: sys.stdout = NullWriter()
if sys.stderr is None: sys.stderr = NullWriter()

def global_exception_handler(exc_type, exc_value, exc_tb):
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    messagebox.showerror("Критична Грешка", f"Нещо се обърка в програмата:\n\n{err_msg}")

sys.excepthook = global_exception_handler
# ----------------------------------------------------

# ⚠️ СЛОЖИ СИ НОВИЯ КЛЮЧ ТУК ⚠️
OPENAI_API_KEY = "your openai api key here"

# --- ФИНА НАСТРОЙКА ---
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

def process_audio_for_playback(data, original_fs, target_fs):
    if len(data.shape) > 1: data = np.mean(data, axis=1)
    if original_fs != target_fs:
        number_of_samples = round(len(data) * float(target_fs) / original_fs)
        data = scipy.signal.resample(data, number_of_samples)
    max_val = np.max(np.abs(data))
    if max_val > 0: data = data / max_val * 0.95
    return data.astype(np.float32)

def check_key_safety(key):
    return not bool(re.search('[а-яА-Я]', key))

class AudioPipeline:
    def __init__(self, app, input_id, output_id, src_lang, trg_lang, name, voice_str):
        self.app = app
        self.input_id = input_id
        self.output_id = output_id
        self.src_code = LANGUAGES[src_lang]
        self.trg_code = LANGUAGES[trg_lang]
        self.name = name
        self.voice_str = voice_str

        self.running = False
        self.process_queue = queue.Queue()
        self.play_queue = queue.Queue()

        self.th_listen = threading.Thread(target=self.listener_loop, daemon=True)
        self.th_process = threading.Thread(target=self.translator_loop, daemon=True)
        self.th_speak = threading.Thread(target=self.speaker_loop, daemon=True)

    def start(self):
        self.running = True
        self.th_listen.start()
        self.th_process.start()
        self.th_speak.start()
        self.app.log(f"🚀 {self.name} RUNNING")

    def stop(self):
        self.running = False
        self.app.log(f"🛑 {self.name} STOPPED")

    def listener_loop(self):
        try:
            dev = sd.query_devices(self.input_id, 'input')
            rate = int(dev['default_samplerate'])
        except:
            rate = 44100

        buffer = []; silent_chunks = 0; is_speaking = False

        def callback(indata, frames, time, status):
            if not self.running: raise sd.CallbackAbort
            vol = np.max(np.abs(indata))
            nonlocal is_speaking, silent_chunks, buffer

            if vol > SILENCE_THRESHOLD:
                if not is_speaking: is_speaking = True
                silent_chunks = 0
                buffer.append(indata.copy())
            else:
                if is_speaking:
                    buffer.append(indata.copy())
                    silent_chunks += 1
                    if (silent_chunks * frames) / rate > SILENCE_DURATION:
                        self.process_queue.put((np.concatenate(buffer, axis=0), rate))
                        buffer = []; is_speaking = False; silent_chunks = 0

        with sd.InputStream(samplerate=rate, device=self.input_id, channels=1, callback=callback):
            while self.running: time.sleep(0.1)

    def translator_loop(self):
        while self.running:
            try:
                try:
                    audio, rate = self.process_queue.get(timeout=0.5)
                except: continue

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                    sf.write(tmp_wav.name, audio, rate)
                    wav_path = tmp_wav.name

                try:
                    with open(wav_path, "rb") as f:
                        tr = self.app.client.audio.transcriptions.create(
                            model="whisper-1", file=f, language=self.src_code, temperature=0.0
                        )
                    text = tr.text
                except Exception as e:
                    os.remove(wav_path)
                    continue
                os.remove(wav_path)

                if not text or len(text) < 2: continue
                if any(p.lower() in text.lower() for p in IGNORED_PHRASES): continue

                self.app.log(f"🗣️ {text}")

                try:
                    gpt = self.app.client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": f"Translate to {self.trg_code}. Output ONLY the translation. Follow these rules: {AI_INSTRUCTIONS}"},
                            {"role": "user", "content": text}
                        ]
                    )
                    translated = gpt.choices[0].message.content
                    self.app.log(f"📝 {translated}")
                except Exception: continue

                try:
                    actual_voice = self.voice_str.split(" ")[0].lower()
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav_tts:
                        wav_tts_path = tmp_wav_tts.name

                    response = self.app.client.audio.speech.create(
                        model="tts-1",
                        voice=actual_voice,
                        input=translated,
                        response_format="wav"
                    )
                    response.stream_to_file(wav_tts_path)
                    self.play_queue.put(wav_tts_path)
                except Exception as e:
                    self.app.log(f"TTS Error: {e}")
            except Exception: pass

    def speaker_loop(self):
        while self.running:
            try:
                try: wav_path = self.play_queue.get(timeout=0.5)
                except: continue

                data, fs = sf.read(wav_path)
                processed = process_audio_for_playback(data, fs, TARGET_SAMPLE_RATE)

                silence_padding = np.zeros(int(TARGET_SAMPLE_RATE * 0.5), dtype=np.float32)
                processed_padded = np.concatenate((processed, silence_padding))

                sd.play(processed_padded, samplerate=TARGET_SAMPLE_RATE, device=self.output_id, blocking=True)
                os.remove(wav_path)
            except: pass

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

class TranslatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.ui_lang, self.voice_out, self.voice_in = load_settings()
        self.t = UI_TEXT[self.ui_lang]

        self.title("Translaty Pro")
        self.window_width = 500
        self.window_height = 800
        self.resizable(False, False)
        self.attributes('-topmost', True)

        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = screen_width - self.window_width - 15
        y = screen_height - self.window_height - 55
        self.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")

        self.pipeline_1 = None
        self.pipeline_2 = None
        self.tray_icon = None

        self.bind("<Unmap>", self.on_minimize)

        if "xxxx" in OPENAI_API_KEY or not check_key_safety(OPENAI_API_KEY):
            self.client = None
            messagebox.showerror(self.t["msg_error"], "Invalid API Key!")
        else:
            try:
                self.client = OpenAI(api_key=OPENAI_API_KEY)
            except:
                self.client = None

        self.create_gui()
        self.populate_devices()

    def on_minimize(self, event):
        if str(event.widget) == str(self) and self.state() == 'iconic':
            self.hide_to_tray()

    def create_tray_icon_image(self):
        image = Image.new('RGB', (64, 64), color=(30, 30, 30))
        draw = ImageDraw.Draw(image)
        draw.ellipse((16, 16, 48, 48), fill=(59, 142, 208))
        return image

    def hide_to_tray(self):
        self.withdraw()
        menu = pystray.Menu(
            pystray.MenuItem(self.t["title"], self.show_from_tray, default=True),
            pystray.MenuItem("Exit", self.quit_app)
        )
        self.tray_icon = pystray.Icon("Translaty", self.create_tray_icon_image(), self.t["title"], menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_from_tray(self, icon, item):
        icon.stop()
        self.after(0, self.restore_window)

    def restore_window(self):
        self.deiconify()
        self.state('normal')

    def quit_app(self, icon, item):
        self.save_current_settings()
        icon.stop()
        self.quit()

    def setup_searchable_combo(self, combo, full_list):
        def on_keyrelease(event):
            if event.keysym in ('BackSpace', 'Left', 'Right', 'Up', 'Down', 'Return'): return
            typed = combo.get().lower()
            if not typed:
                combo.configure(values=full_list)
            else:
                filtered = [item for item in full_list if typed in item.lower()]
                combo.configure(values=filtered)

        combo._entry.bind('<KeyRelease>', on_keyrelease)

    def change_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def save_current_settings(self, _=None):
        save_settings(self.combo_ui_lang.get(), self.combo_voice_out.get(), self.combo_voice_in.get())

    def change_ui_language(self, choice):
        self.save_current_settings()
        messagebox.showinfo("Translaty Pro", self.t["msg_restart"])

    def create_gui(self):
        title_label = ctk.CTkLabel(self, text=self.t["title"], font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(15, 10))

        self.tabview = ctk.CTkTabview(self, width=470, height=440)
        self.tabview.pack(padx=15, pady=5, fill="both")

        self.tabview.add(self.t["tab_out"])
        self.tabview.add(self.t["tab_in"])
        self.tabview.add(self.t["tab_set"])
        self.tabview.add(self.t["tab_faq"])

        tab1 = self.tabview.tab(self.t["tab_out"])
        ctk.CTkLabel(tab1, text=self.t["i_speak"], font=ctk.CTkFont(size=14)).pack(pady=(15, 5))
        self.l_me = ctk.CTkComboBox(tab1, values=ALL_LANG_NAMES, width=250, font=ctk.CTkFont(size=14))
        self.l_me.set("Bulgarian")
        self.setup_searchable_combo(self.l_me, ALL_LANG_NAMES)
        self.l_me.pack(pady=5)

        ctk.CTkLabel(tab1, text=self.t["translates_to"], text_color="#3a7ebf", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=10)

        self.l_them = ctk.CTkComboBox(tab1, values=ALL_LANG_NAMES, width=250, font=ctk.CTkFont(size=14))
        self.l_them.set("English")
        self.setup_searchable_combo(self.l_them, ALL_LANG_NAMES)
        self.l_them.pack(pady=5)

        self.btn_out = ctk.CTkButton(tab1, text=self.t["btn_start_trans"], font=ctk.CTkFont(size=14, weight="bold"), height=40, command=self.toggle_out)
        self.btn_out.pack(pady=30)

        tab2 = self.tabview.tab(self.t["tab_in"])
        ctk.CTkLabel(tab2, text=self.t["they_speak"], font=ctk.CTkFont(size=14)).pack(pady=(15, 5))
        self.l_them_src = ctk.CTkComboBox(tab2, values=ALL_LANG_NAMES, width=250, font=ctk.CTkFont(size=14))
        self.l_them_src.set("German")
        self.setup_searchable_combo(self.l_them_src, ALL_LANG_NAMES)
        self.l_them_src.pack(pady=5)

        ctk.CTkLabel(tab2, text=self.t["translates_to"], text_color="#3a7ebf", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=10)

        self.l_me_trg = ctk.CTkComboBox(tab2, values=ALL_LANG_NAMES, width=250, font=ctk.CTkFont(size=14))
        self.l_me_trg.set("Bulgarian")
        self.setup_searchable_combo(self.l_me_trg, ALL_LANG_NAMES)
        self.l_me_trg.pack(pady=5)

        self.btn_in = ctk.CTkButton(tab2, text=self.t["btn_start_listen"], font=ctk.CTkFont(size=14, weight="bold"), height=40, command=self.toggle_in)
        self.btn_in.pack(pady=30)

        tab3 = self.tabview.tab(self.t["tab_set"])

        top_frame = ctk.CTkFrame(tab3, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=(5, 5))

        lang_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        lang_frame.pack(side="left", expand=True)
        ctk.CTkLabel(lang_frame, text=self.t["lbl_ui_lang"], font=ctk.CTkFont(weight="bold")).pack(pady=(0, 2))
        self.combo_ui_lang = ctk.CTkComboBox(lang_frame, values=["English", "Bulgarian", "German"], command=self.change_ui_language, width=140)
        self.combo_ui_lang.set(self.ui_lang)
        self.combo_ui_lang.pack()

        voice_out_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        voice_out_frame.pack(side="left", expand=True)
        ctk.CTkLabel(voice_out_frame, text=self.t["lbl_voice_out"], font=ctk.CTkFont(weight="bold"), text_color="#3a7ebf").pack(pady=(0, 2))
        self.combo_voice_out = ctk.CTkComboBox(voice_out_frame, values=OPENAI_VOICES, command=self.save_current_settings, width=140)
        self.combo_voice_out.set(self.voice_out)
        self.combo_voice_out.pack()

        voice_in_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        voice_in_frame.pack(side="right", expand=True)
        ctk.CTkLabel(voice_in_frame, text=self.t["lbl_voice_in"], font=ctk.CTkFont(weight="bold"), text_color="#28a745").pack(pady=(0, 2))
        self.combo_voice_in = ctk.CTkComboBox(voice_in_frame, values=OPENAI_VOICES, command=self.save_current_settings, width=140)
        self.combo_voice_in.set(self.voice_in)
        self.combo_voice_in.pack()

        self.theme_switch = ctk.CTkSwitch(tab3, text=self.t["lbl_theme"], command=self.change_theme)
        self.theme_switch.pack(pady=(15, 10))
        if darkdetect.isDark():
            self.theme_switch.select()
        else:
            self.theme_switch.deselect()

        ctk.CTkLabel(tab3, text=self.t["lbl_mic"]).pack(anchor="w", padx=20, pady=(0, 0))
        self.combo_mic = ctk.CTkComboBox(tab3, width=350, state="readonly");
        self.combo_mic.pack(padx=20, pady=2)

        ctk.CTkLabel(tab3, text=self.t["lbl_cab_in"]).pack(anchor="w", padx=20, pady=(0, 0))
        self.combo_cable_in = ctk.CTkComboBox(tab3, width=350, state="readonly");
        self.combo_cable_in.pack(padx=20, pady=2)

        ctk.CTkFrame(tab3, height=2, fg_color="gray30").pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(tab3, text=self.t["lbl_cab_out"]).pack(anchor="w", padx=20, pady=(0, 0))
        self.combo_cable_out = ctk.CTkComboBox(tab3, width=350, state="readonly");
        self.combo_cable_out.pack(padx=20, pady=2)

        ctk.CTkLabel(tab3, text=self.t["lbl_ph"]).pack(anchor="w", padx=20, pady=(0, 0))
        self.combo_ph = ctk.CTkComboBox(tab3, width=350, state="readonly");
        self.combo_ph.pack(padx=20, pady=2)

        tab4 = self.tabview.tab(self.t["tab_faq"])
        faq_textbox = ctk.CTkTextbox(tab4, width=400, height=300, font=ctk.CTkFont(size=13), wrap="word")
        faq_textbox.pack(padx=10, pady=10, fill="both", expand=True)
        faq_textbox.insert("0.0", self.t["faq_content"])
        faq_textbox.configure(state="disabled")

        self.log_area = ctk.CTkTextbox(self, width=420, height=130, font=ctk.CTkFont("Consolas", size=12))
        self.log_area.pack(padx=15, pady=5, fill="both", expand=True)
        self.log_area.configure(state="disabled")

    def log(self, msg, msg_type="normal"):
        self.after(0, self._log_internal, msg, msg_type)

    def _log_internal(self, msg, msg_type):
        self.log_area.configure(state="normal")
        self.log_area.insert("end", msg + "\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    def populate_devices(self):
        sd._terminate(); sd._initialize()
        apis = sd.query_hostapis()
        mme_index = next((i for i, a in enumerate(apis) if "MME" in a['name']), -1)
        devs = sd.query_devices()
        in_d, out_d = [], []
        for i, d in enumerate(devs):
            if d['hostapi'] == mme_index:
                name = f"{i}: {d['name']}"
                if d['max_input_channels'] > 0: in_d.append(name)
                if d['max_output_channels'] > 0: out_d.append(name)

        if not in_d: in_d = ["Няма устройства"]
        if not out_d: out_d = ["Няма устройства"]

        self.combo_mic.configure(values=in_d); self.combo_cable_out.configure(values=in_d)
        self.combo_cable_in.configure(values=out_d); self.combo_ph.configure(values=out_d)

        for d in in_d:
            if "Microphone" in d: self.combo_mic.set(d)
            if "CABLE-B Output" in d: self.combo_cable_out.set(d)
        for d in out_d:
            if "CABLE-A Input" in d: self.combo_cable_in.set(d)
            if "Headphones" in d: self.combo_ph.set(d)

    def get_id(self, v):
        try: return int(v.split(":")[0])
        except: return None

    def toggle_out(self):
        if not self.client: return messagebox.showerror(self.t["msg_error"], "Missing API Key!")
        self.save_current_settings()

        if self.pipeline_1 and self.pipeline_1.running:
            self.pipeline_1.stop()
            self.btn_out.configure(text=self.t["btn_start_trans"], fg_color=["#3B8ED0", "#1F6AA5"], hover_color=["#36719F", "#144870"])
        else:
            in_id, out_id = self.get_id(self.combo_mic.get()), self.get_id(self.combo_cable_in.get())
            if in_id is None or out_id is None: return messagebox.showerror(self.t["msg_error"], self.t["msg_no_devices"])

            self.pipeline_1 = AudioPipeline(self, in_id, out_id, self.l_me.get(), self.l_them.get(), "Поток 1", self.combo_voice_out.get())
            self.pipeline_1.start()
            self.btn_out.configure(text=self.t["btn_stop"], fg_color="#c93434", hover_color="#9e2a2a")

    def toggle_in(self):
        if not self.client: return messagebox.showerror(self.t["msg_error"], "Missing API Key!")
        self.save_current_settings()

        if self.pipeline_2 and self.pipeline_2.running:
            self.pipeline_2.stop()
            self.btn_in.configure(text=self.t["btn_start_listen"], fg_color=["#3B8ED0", "#1F6AA5"], hover_color=["#36719F", "#144870"])
        else:
            in_id, out_id = self.get_id(self.combo_cable_out.get()), self.get_id(self.combo_ph.get())
            if in_id is None or out_id is None: return messagebox.showerror(self.t["msg_error"], self.t["msg_no_devices"])

            self.pipeline_2 = AudioPipeline(self, in_id, out_id, self.l_them_src.get(), self.l_me_trg.get(), "Поток 2", self.combo_voice_in.get())
            self.pipeline_2.start()
            self.btn_in.configure(text=self.t["btn_stop"], fg_color="#c93434", hover_color="#9e2a2a")

if __name__ == "__main__":
    app = TranslatorApp()
    app.mainloop()