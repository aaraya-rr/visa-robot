# Visa Appointment Monitor (Linux)

This script monitors the US visa scheduling website for available appointment dates. Once a slot is detected, it emits a beep and sends a desktop notification.

---

## ✅ Features

* Logs in automatically using credentials from a config file.
* Periodically refreshes the calendar to detect new appointment slots.
* Plays a sound and sends a notification when a date is available.
* Handles common site issues (e.g., maintenance or loading errors) by retrying and refreshing the page.
* Allows configurable limits and retry behavior via `config.ini`.

---

## 🚀 Quick Start

1. **Create a virtual environment (optional but recommended):**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the `config.ini` file:**

   In the project root, create a file named `config.ini` with the following contents:

   ```ini
   [credentials]
   email = your_email@example.com
   password = your_secure_password

   [settings]
   max_year = 2025
   max_month = 10
   max_day = 31
   max_calendar_attempts = 5
   ```

4. **Install system packages (if not already installed):**

   ```bash
   sudo apt install pulseaudio-utils alsa-utils libnotify-bin
   ```

5. **Run the script:**

   ```bash
   python visa_bot.py
   ```

---

## ⚙️ Configuration Reference

* **email / password**: Your credentials for the visa appointment site.
* **max\_year / max\_month / max\_day**: The latest date to check for available appointments.
* **max\_calendar\_attempts**: Number of retries when the calendar fails to load before restarting login.

All of these values are required in `config.ini`.

---

## 📦 Dependencies

Listed in `requirements.txt`:

```
selenium==4.31.0
```

Also requires:

* **Google Chrome** and **ChromeDriver** installed and available in `PATH`.

---

## 🛡️ Error Handling

The script is designed to recover from:

* Session timeouts
* Page maintenance messages
* Calendar UI not loading
* Unexpected crashes

It restarts the login process automatically when needed and continues monitoring without manual intervention.