# TruthLens Data Storage Directory

This directory (`storage/`) houses the persistent local data layer for **TruthLens**.

## 1. Files Stored in this Directory
- `truthlens.db`: The active SQLite database storing analysis history, extracted claims, and detected rhetorical techniques.
- `.gitkeep`: Git placeholder ensuring this directory exists in clean checkouts.
- `README.md`: This documentation guide.

## 2. What Information is Stored
The database stores only operational metadata and structured findings necessary to display the dashboard and history:
- Analysis record identifier (UUID)
- Article title or short preview snippet (truncated for privacy)
- Source URL (if analyzed from URL)
- Detected language (English, Hindi, Telugu, Punjabi)
- Structured AI analysis (JSON containing summary, framing indicators, limitations)
- Extracted factual claims and their verification status
- Evidence source citations (when genuinely retrieved from open search/knowledge bases)
- Timestamp of analysis

**Security & Privacy Guarantee**:
- **No API keys or credentials** are ever written to this database or any storage file.
- Full raw articles are **not permanently stored**; only the structured analytical breakdown is retained.

## 3. How to Inspect Records
You can inspect the database using any of the following methods:

### Method A: Built-in Command Line Utility
Run the inspection script from the project root:
```bash
python scripts/inspect_database.py
```

### Method B: SQLite Command Line
```bash
sqlite3 storage/truthlens.db
.tables
SELECT id, title, language, status, created_at FROM analyses ORDER BY created_at DESC LIMIT 5;
.quit
```

### Method C: Graphical Tools
Open `storage/truthlens.db` using free desktop applications:
- **DB Browser for SQLite** (https://sqlitebrowser.org/)
- **DBeaver** or **VS Code SQLite Viewer Extension**

## 4. How to Back Up the Database
Because SQLite uses a single file, backup is simple and atomic:
1. Ensure the TruthLens application is not actively processing a request.
2. Copy `storage/truthlens.db` to a backup location:
   ```cmd
   copy storage\truthlens.db storage\truthlens_backup_%DATE%.db
   ```

## 5. How to Delete Stored Analyses
- **Single Analysis Deletion**: Use the red "Delete" button on the **History** or **Results** page in the TruthLens web interface.
- **Bulk Reset**: Run the reset script:
  ```bash
  python scripts/init_database.py --reset
  ```

## 6. How to Safely Reset the Database
If you wish to wipe all past data and start completely fresh:
1. Stop the running TruthLens server (Ctrl+C in terminal).
2. Delete the file `storage/truthlens.db` or run:
   ```cmd
   python scripts/init_database.py --reset
   ```
3. Restart TruthLens. The application will automatically regenerate a fresh, clean database schema.
