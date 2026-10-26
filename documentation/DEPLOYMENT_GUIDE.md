# TruthLens Deployment & GitHub Publishing Guide

This guide provides step-by-step instructions to publish **TruthLens** to GitHub under your profile (`https://github.com/shaikcharan`) and deploy it to **Vercel** with continuous integration (CI/CD).

---

## 1. Project Architecture for Vercel

TruthLens is configured for seamless deployment on Vercel's Serverless Python runtime:

- **Entrypoint:** `api/index.py` exposes the Flask WSGI `app` to Vercel's serverless handler.
- **Routing:** `vercel.json` rewrites all incoming traffic (`/(.*)`) to the serverless entrypoint.
- **Serverless SQLite Compatibility:** On Vercel, the local container filesystem is read-only except for `/tmp`. TruthLens automatically detects the Vercel serverless environment (`VERCEL=1`) and routes SQLite transactions to `/tmp/truthlens.db`, ensuring zero-crash initialization and live analytical persistence.
- **Bundled Static Assets:** CSS, Vanilla JS, locally-hosted Chart.js, and photography assets are served directly through the Flask WSGI layer with appropriate MIME headers.

---

## 2. Pushing TruthLens to GitHub

### Step 2.1: Create a New Repository on GitHub
1. Open your browser and log into [GitHub](https://github.com/).
2. Navigate to [https://github.com/new](https://github.com/new).
3. Set the **Repository name** to `TruthLens` (or `Multilingual-Fake-News-Propaganda-Analyzer`).
4. Set visibility to **Public** (or **Private** based on preference).
5. **Do NOT** check "Add a README file", ".gitignore", or "license" (TruthLens already has production-ready versions of these).
6. Click **Create repository**.
7. Copy your repository URL, which will look like:
   ```text
   https://github.com/shaikcharan/TruthLens.git
   ```

### Step 2.2: Initialize and Push from Your Terminal
Open PowerShell or Command Prompt in the `TruthLens_Project` folder:

```powershell
# Navigate into the project folder
cd "c:\Users\HP\OneDrive\Pictures\Desktop\Multilingual Fake News & Propaganda Analyzer\TruthLens_Project"

# Initialize local Git repository (if not already initialized)
git init

# Set default branch to main
git branch -M main

# Stage all project files (secrets in .env and caches are automatically ignored by .gitignore)
git add .

# Create the initial commit
git commit -m "feat: complete TruthLens multilingual news analyzer with Vercel deployment configuration"

# Add your GitHub repository as remote origin
git remote add origin https://github.com/shaikcharan/TruthLens.git

# Push to GitHub
git push -u origin main
```

*(Note: If prompted, authenticate using your GitHub login or Personal Access Token in the Git Credential Manager window).*

---

## 3. Deploying to Vercel (1-Click GitHub Integration)

This is the recommended method. Once connected, every `git push` to your GitHub repository will automatically trigger a new deployment.

### Step 3.1: Import Your Repository
1. Go to [https://vercel.com/](https://vercel.com/) and sign in with your GitHub account.
2. In your Vercel Dashboard, click **Add New...** -> **Project**.
3. Under **Import Git Repository**, find your `TruthLens` repository and click **Import**.

### Step 3.2: Configure Project Settings
- **Project Name:** `truthlens` (or leave as default)
- **Framework Preset:** `Other` (Vercel automatically detects Python via `requirements.txt`)
- **Root Directory:** `./` (leave default if you pushed `TruthLens_Project` directly)

### Step 3.3: Set Environment Variables
In the **Environment Variables** section on Vercel, add the following variables:

| Variable Name | Recommended Value | Purpose |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | `AIzaSy...` *(Your Gemini API key)* | Enables live AI reasoning and factual claim extraction. |
| `SECRET_KEY` | *(A random 32-character string)* | Secures Flask sessions and flash messages. |
| `ENABLE_FACT_CHECK_SEARCH` | `true` | Enables real-time Wikipedia corroboration. |

> **Note:** If `GEMINI_API_KEY` is omitted, TruthLens will automatically operate in **Deterministic Offline/Mock Mode**, analyzing articles using local heuristics without throwing errors.

### Step 3.4: Deploy
1. Click the blue **Deploy** button.
2. Vercel will install dependencies from `requirements.txt`, build the serverless functions, and output your live production URL (e.g., `https://truthlens-xxx.vercel.app`).
3. Open the production URL in your browser to verify the homepage, dashboard, and analysis studio!

---

## 4. Alternative Method: Deploying via Vercel CLI

If you prefer deploying directly from your local terminal without connecting GitHub:

```powershell
# Navigate into the project folder
cd "c:\Users\HP\OneDrive\Pictures\Desktop\Multilingual Fake News & Propaganda Analyzer\TruthLens_Project"

# Deploy using npx (no global install required)
npx vercel
```

Follow the interactive prompts:
1. `Set up and deploy?` -> `Y`
2. `Which scope?` -> Select your personal Vercel account
3. `Link to existing project?` -> `N`
4. `What's your project's name?` -> `truthlens`
5. `In which directory is your code located?` -> `./`

To deploy to production directly:
```powershell
npx vercel --prod
```

---

## 5. Cloud vs. Local Differences (Viva / Capstone Reference)

When explaining this deployment to evaluators:

1. **Local Execution (Port 8765):**
   - SQLite is stored permanently at `storage/truthlens.db`.
   - Uses dedicated Port 8765 exclusively for process isolation.
   - 100% offline capable (uses local Chart.js, local heuristics, and local mock database).

2. **Vercel Serverless Function:**
   - AWS Lambda / Vercel serverless micro-containers run Python on demand.
   - Filesystem is ephemeral and read-only, with `/tmp` allocated for temporary database writes.
   - For enterprise-grade permanent cloud persistence across server restarts, SQLite can be swapped for a hosted PostgreSQL (Supabase/Neon) or distributed libSQL (Turso) by setting the `DATABASE_URL` connection string.
