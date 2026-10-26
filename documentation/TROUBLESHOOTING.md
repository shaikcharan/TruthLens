# TruthLens Troubleshooting & Operational FAQ

This guide explains how to identify, resolve, and prevent common operational errors when deploying or demonstrating TruthLens.

---

## 1. Port 8765 is Already in Use

### Symptom:
When starting `app.py` or running `RUN_TRUTHLENS.bat`, you see:
```text
Port 8765 is already in use. Close the existing TruthLens instance or select a different port in config.py.
```

### Cause:
Another instance of TruthLens or an unrelated service is already listening on TCP port 8765.

### Resolution:
**Option A: Terminate the existing TruthLens process**
1. On Windows, open Command Prompt or PowerShell:
   ```cmd
   netstat -ano | findstr :8765
   ```
2. Note the Process ID (`PID`) in the rightmost column (e.g., `12344`).
3. Terminate the process:
   ```cmd
   taskkill /PID 12344 /F
   ```

**Option B: Change the port in `config.py`**
Open `config.py` (or `.env`) and update the port number:
```python
PORT = int(os.getenv("PORT", 8766))
```

---

## 2. Gemini API Key Missing or Invalid

### Symptom:
The settings page displays:
`Not Configured (Running in Offline / Mock Mode)`
or an API error occurs during analysis.

### Cause:
`GEMINI_API_KEY` has not been set in the `.env` file, or the key is inactive.

### Resolution:
1. Ensure your `.env` file exists in the root of `TruthLens_Project/`. If missing:
   ```cmd
   copy .env.example .env
   ```
2. Open `.env` and paste your key without quotes:
   ```env
   GEMINI_API_KEY=AIzaSyB...YourActualKey...
   ```
3. Test your configuration:
   ```bash
   python scripts/check_environment.py
   ```
4. Restart TruthLens. If no key is available, TruthLens will seamlessly function in **Offline Demonstration Mode** without crashing.

---

## 3. Windows PowerShell Script Execution Policy Error

### Symptom:
When running batch scripts or activating `.venv` in PowerShell, you receive:
`...cannot be loaded because running scripts is disabled on this system.`

### Cause:
Windows PowerShell restricts running unsigned `.ps1` scripts by default.

### Resolution:
Run the script using Command Prompt (`cmd.exe`) or adjust the execution policy for your current user:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Alternatively, launch TruthLens directly using Python without activating the shell:
```cmd
.\.venv\Scripts\python.exe app.py
```

---

## 4. URL Extraction Fails or Returns Security Notice

### Symptom:
When analyzing a URL, you receive:
- `Security Notice: Access to host is prohibited: Private or local IP range.`
- `Content Extraction Error: Website returned HTTP status 403.`

### Cause:
- **SSRF Defense:** The URL points to `localhost`, `127.0.0.1`, or an internal network IP address (`192.168.x.x`, `10.x.x.x`). TruthLens strictly blocks these destinations to prevent network probing.
- **Paywalls & Cloudflare:** Some commercial news websites (like NYTimes or paywalled portals) require subscription logins or active JavaScript rendering.

### Resolution:
- For paywalled articles, copy the article text directly and use the **Paste Article Text** tab on the homepage.
- For local testing, paste the news text directly rather than attempting to point to a local test server.

---

## 5. Database Locked or Corrupted

### Symptom:
`sqlite3.OperationalError: database is locked`

### Cause:
A previous Python process crashed while holding an active write transaction, or the file is open exclusively in a desktop database browser.

### Resolution:
1. Close any SQLite GUI tools (such as DB Browser for SQLite) that have `storage/truthlens.db` open.
2. If necessary, reset the database safely:
   ```bash
   python scripts/init_database.py --reset
   ```

---

## 6. Pre-Flight Diagnostic Check

Whenever in doubt, run the automated environment diagnostics utility:
```bash
python scripts/check_environment.py
```
This utility checks Python version, all package imports, port availability, database schema integrity, and API key status in one unified report.
