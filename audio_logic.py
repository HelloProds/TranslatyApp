import sys
import traceback
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import sounddevice as sd
from openai import OpenAI
import threading
import warnings
import pystray
from PIL import Image, ImageDraw
import darkdetect

# Импортираме логиката и конфигурациите от другите файлове
from config import (OPENAI_API_KEY, UI_TEXT, ALL_LANG_NAMES, OPENAI_VOICES,
                    load_settings, save_settings, check_key_safety)
from audio_logic import AudioPipeline

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
        self.combo_mic = ctk.CTkComboBox(tab3, width=350, state="readonly")
        self.combo_mic.pack(padx=20, pady=2)

        ctk.CTkLabel(tab3, text=self.t["lbl_cab_in"]).pack(anchor="w", padx=20, pady=(0, 0))
        self.combo_cable_in = ctk.CTkComboBox(tab3, width=350, state="readonly")
        self.combo_cable_in.pack(padx=20, pady=2)

        ctk.CTkFrame(tab3, height=2, fg_color="gray30").pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(tab3, text=self.t["lbl_cab_out"]).pack(anchor="w", padx=20, pady=(0, 0))
        self.combo_cable_out = ctk.CTkComboBox(tab3, width=350, state="readonly")
        self.combo_cable_out.pack(padx=20, pady=2)

        ctk.CTkLabel(tab3, text=self.t["lbl_ph"]).pack(anchor="w", padx=20, pady=(0, 0))
        self.combo_ph = ctk.CTkComboBox(tab3, width=350, state="readonly")
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
