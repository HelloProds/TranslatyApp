<div align="center">

# 🎙️ Translaty Pro
### Real-Time Bi-Directional Voice Translator

[![OS Support](https://img.shields.io/badge/OS-Windows_10%20%7C%2011-0078D6?style=for-the-badge&logo=windows)](https://microsoft.com)
[![AI Engine](https://img.shields.io/badge/AI_Engine-OpenAI_GPT--4o-412991?style=for-the-badge&logo=openai)](https://openai.com)
[![Status](https://img.shields.io/badge/Status-Ready_to_use-2EA043?style=for-the-badge)]()

**Break the language barrier.** Translaty Pro is a desktop application that translates your voice and your conversation partners' voices instantly during calls. It works directly at the operating system level, making it compatible with **any** communication platform: Discord, Zoom, Microsoft Teams, Meets, TeamSpeak, and more.


---
</div>

## ✨ Key Features

Translaty Pro is designed to provide high-quality translation without disrupting your workflow or gaming experience:
- 🧠 **Context-Aware Translation:** Uses GPT-4o to understand the context of your sentence, correcting phonetic errors from your microphone before executing the translation.
- 🗣️ **Natural Voice Synthesis:** Generates realistic human-like speech, slightly accelerated to compensate for natural conversational delays.
- 🪶 **Low Resource Consumption:** All heavy AI processing is handled in the cloud. The application uses less than 100MB of RAM and has minimal CPU impact, making it perfect to run alongside heavy games or software.

---

## 📥 Download & Installation

Everything is packaged into a single executable file. No coding or complex setup required.

### 🔗 [Download Translaty](https://github.com/HelloProds/TranslatyApp/releases/tag/v1.0.0)

> **⚠️ Note:** To route audio to applications like Discord or Zoom, the software requires Virtual Audio Cables. The installer will automatically check your system and install them in the background if they are missing.

**Installation Steps:**
1. Download the `Translaty_Setup.exe` file from the link above.
2. Run the installer and follow the on-screen instructions.
3. Open the application from your desktop shortcut.

---

## 🎧 Setup Guide (Discord / Zoom / etc)

To enable real-time translation, you need to tell Windows where to route the audio. 

### 🌐 Scenario 1: You speak a foreign language (Outgoing Translation)
*You speak in your native language, and your friends hear the translated voice.*
* **In Translaty:** Set `Microphone` ➔ Your actual hardware microphone.
* **In Translaty:** Set `Output Cable` ➔ `CABLE-A Input`.
* **In Discord/Zoom:** Go to Voice Settings and set `Input Device (Microphone)` ➔ `CABLE-A Output`.

### 🌐 Scenario 2: Translate what others are saying (Incoming Translation)
*Your friends speak a foreign language, and you hear the translation in your headphones.*
* **In Discord/Zoom:** Set `Output Device (Speaker)` ➔ `CABLE-B Input`.
* **In Translaty:** Set `Input Cable` ➔ `CABLE-B Output`.
* **In Translaty:** Set `Headphones` ➔ Your actual headphones.

---

## 💻 Interface & Usability

- 🌙 **Dark/Light Mode:** Automatically adapts to your Windows system theme.
- 🔍 **Quick Search:** Easily find your target language from the drop-down menu just by typing.
- 🛡️ **Background Operation:** Minimize the app to the System Tray to keep your screen clear while talking.
- 📡 **Live Terminal:** Monitor the transcribed text and real-time translation process directly in the app's built-in console.

---

## 🛠️ Build it Yourself

If you wish to modify the source code and compile your own standalone `.exe` without using the pre-built installer, follow these steps:

**1. Clone the repository**
`bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
`

**2. Enter your OpenAI API key**
Replace the text in config.py and main.py with your OpenAI API key.

**3. Install requirements & PyInstaller**
Ensure you have Python installed, then install the required libraries along with the compilation tool:
` bash
pip install -r requirements.txt
pip install pyinstaller
`

**4. Compile the code**
Since the project relies on a modular architecture, you only need to point PyInstaller to the `main.py` entry file. It will automatically link `config.py` and `audio_logic.py`. Run the following command in your terminal:
`bash
pyinstaller --noconsole --onefile main.py
`
*(The `--noconsole` flag ensures the app runs purely via the GUI without a background terminal, and `--onefile` packages everything into a single executable).*

**5. Run your build**
Once the process finishes successfully, your compiled executable will be located inside the newly generated `dist/` folder. You can rename `main.exe` to `TranslatyPro.exe` and run it directly.

<div align="center">

</div>
