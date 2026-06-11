# AutoService Call Analyzer

An automated pipeline that transcribes phone call recordings from Google Drive, analyzes conversations using AI, and writes structured quality control reports directly to Google Sheets — built as a production-ready solution for auto service business call monitoring.

---

## Overview

Auto service businesses handle dozens of inbound calls daily. Manually reviewing each call for quality control is time-consuming and inconsistent. This tool automates the entire process:

- Detects new, unprocessed audio files in a source Google Drive folder
- Copies them to a working folder and transcribes each call using OpenAI Whisper
- Sends the transcription to GPT for structured analysis — extracting call metadata, checklist completion, work type, outcome, and a manager quality score
- Appends a structured row to a Google Sheets report, ready for review

---

## How It Works

```
Source Google Drive Folder
        │
        ▼
  Detect unprocessed audio files
  (compared against Google Sheets log)
        │
        ▼
  Copy audio to working folder
        │
        ▼
  Transcribe with OpenAI Whisper (local)
        │
        ▼
  Save .txt transcription next to audio
        │
        ▼
  Analyze dialogue with GPT-4o-mini
  (greeting, car info, diagnostics offer,
   appointment, work type, manager score...)
        │
        ▼
  Calculate operation score
  (40% checklist + 60% GPT manager score)
        │
        ▼
  Append row to Google Sheets report
```

---

## Caching & Deduplication

Each processed call is saved locally as a `.json` file in `output/` using the 
universal audio ID as the filename. On every run, the pipeline checks this cache 
before processing:

**If a local `.json` cache exists:**
- Builds the Sheets row directly from cached data — no API calls needed
- If the audio file is missing from Drive → re-copies it and updates the cache
- If the `.txt` transcription is missing from Drive → re-uploads it from cache

**If no cache exists (new file):**
- Checks Drive inventory for existing `.txt` transcription
- If `.txt` exists → downloads and reuses it, skips Whisper transcription
- If no `.txt` → runs full Whisper transcription and uploads result
- Runs GPT analysis → saves result to local `.json` cache

This means:
- Re-running the pipeline never re-processes already analyzed calls
- Deleted Sheets rows are safely recovered from cache on next run
- Whisper is only called when truly needed

---

## Project Structure

```
.
├── config/
│   ├── .env                  # API keys and secrets (not tracked)
│   ├── .env.example          # Environment variable template
│   ├── config.py             # All project constants and configuration
│   ├── credentials.json      # Google OAuth credentials (not tracked)
│   └── token.json            # Auto-generated Google OAuth token (not tracked)
│
├── log/
│   ├── logger_config.py      # Logging setup (file + console)
│   └── parser.log            # Runtime log (not tracked)
│
├── src/
│   ├── analyzer.py           # GPT dialogue analysis via OpenAI API
│   ├── prompts.py            # System and user prompt builders
│   ├── sheets_writer.py      # Score calculation and row builder for Sheets
│   ├── transcriber.py        # Whisper model loader and transcription
│   ├── utils.py              # Filename parser and report backup utility
│   └── google/
│       ├── auth.py           # Google OAuth flow and service builders
│       ├── drive.py          # Drive operations (upload, download, copy, list)
│       └── sheets.py         # Sheets operations (read, write, index lookup)
│
├── main.py                   # Pipeline entry point
├── pyproject.toml            # Poetry project config and dependencies
└── poetry.lock
```

---

## Requirements

- Python 3.10+
- [Poetry](https://python-poetry.org/) for dependency management
- A Google Cloud project with Drive and Sheets APIs enabled
- An OpenAI API key

**Key dependencies:**

| Package | Purpose |
|---|---|
| `openai-whisper` | Local audio transcription |
| `openai` | GPT dialogue analysis |
| `google-api-python-client` | Google Drive & Sheets API |
| `google-auth-oauthlib` | Google OAuth 2.0 flow |
| `python-dotenv` | Environment variable loading |
| `certifi` | Carefully handles SSL/TLS certificates for secure API requests |
---

## Google API Setup

Go to the following link to create and configure your own Google API project:
https://console.cloud.google.com/projectselector2/apis/dashboard

In the **Enabled APIs & services** block, click **Create project**. In the **New Project** dialog, enter a project name and click **Create**.

Once the project is created, you'll be taken to the **APIs & Services** dashboard. Click **+ Enable APIs and services**.

Use the search bar to find **Google Drive API**, then click on it *(Create and manage resources in Google Drive)* and click **Enable**.

Repeat the same process to enable **Google Sheets API**.

After enabling the Google Sheets API, click **Create credentials** on the right side of the screen.

In the credentials setup flow:

**1. Credential Type** — leave *Select an API* as is, choose **User data**, then click **Next**.

**2. OAuth Consent Screen** — fill in **App name**, **User support email**, and **Developer contact information** with your email. Click **Save and continue**.
> This step may not always appear — you might be taken directly to **Scopes**.

**3. Scopes** — skip this step and click **Next**.

**4. OAuth Client ID** — set **Application type** to **Desktop app**, enter a **Name**, and click **Create**.

In the **Your Credentials** section, download the file under **Client ID** and place it in the `audio_analizer/config/` directory. Rename the file to `credentials.json`.

Click **Done** to finish.

---

**Adding a test user**

Go to:
https://console.cloud.google.com/projectselector2/auth/overview

In the left sidebar, select **Audience**. Scroll down to the **Test users** block, click **Add user**, enter your email, and click **Save**.

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/denysdontsu/audio_analizer.git 
cd audio_analizer
```

---

### 2. Install ffmpeg

Whisper requires ffmpeg to process audio files.

**macOS:**
```bash
brew install ffmpeg
```

> If you don't have Homebrew installed: https://brew.sh

**Windows:**
```bash
winget install ffmpeg
```

> After installation, restart your terminal so `ffmpeg` is available in PATH. You can verify with `ffmpeg -version`.

---

### 3. Fix Python SSL certificates (macOS only)

On macOS, Python installed from python.org may fail to make HTTPS requests due to missing SSL certificates. To fix this, find your Python version first:

```bash
which python3
```

Then run the certificate installer for your version. Replace `3.x` with your actual version (e.g. `3.12`):

```bash
open /Applications/Python\ 3.x/Install\ Certificates.command
```

> Skip this step on Windows or if you installed Python via Homebrew/pyenv.

---

### 4. Install dependencies

This project uses [Poetry](https://python-poetry.org/) for dependency management.

**Install Poetry** (if not already installed):

```bash
# macOS / Linux
curl -sSL https://install.python-poetry.org | python3 -

# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

**Install project dependencies:**

```bash
poetry install
```

---

### 5. Get an OpenAI API key

1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click **Create new secret key**, give it a name, and click **Create**
4. Copy the key — you won't be able to see it again

> Make sure your OpenAI account has billing set up. Even small-scale usage of `gpt-4o-mini` is very cheap, but the API requires a funded account to work.

---

### 6. Set up Google Drive Configuration

The pipeline automatically handles the deployment of the report spreadsheet and working directories. You only need to provide a single destination folder ID.

1. **Create or choose a destination folder** in your Google Drive. This folder will hold the generated report spreadsheet, downloaded audio files, and text transcripts.
2. Open this folder in your browser and copy its ID from the URL:
```
https://drive.google.com/drive/folders/YOUR_FOLDER_ID_HERE
```
3. Save this ID as `TARGET_PARENT_ID` in your `.env` file.

*Note: On the very first run, the script will automatically copy the master template Google Sheet into this folder, setup the required subfolders for audio processing, and handle everything dynamically.*

---

### 7. Configure the project

**Set up environment variables:**

```bash
cp config/.env.example config/.env
```

Open `config/.env` and fill in your OpenAI API key:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

**Set up `config/config.py` constants:**

Open `config/config.py` and configure the folder IDs:

Note: For the testing environment, predefined source IDs are already provided in the code, but make sure to paste your destination ID:
```python
# 1. Paste your destination folder ID here (gathered from Step 6)
TARGET_PARENT_ID = 'your_working_folder_id'  

# 2. Keep these as they are (preconfigured test source folders provided for the review)
SOURCE_FOLDER_ID = '17_zO...'  # Predefined folder containing test audio files
SOURCE_SHEET_ID  = '17rTX...'  # Master template Google Sheet with pre-styled headers
```

On the very first run, the pipeline will automatically copy the master template sheet into your target folder, create the required audio subdirectories, and handle the rest of the execution dynamically.

See the [Configuration](#configuration) section below for a full description of all constants.

---

### 8. Complete Google API setup

Follow the [Google API Setup](#google-api-setup) section to create a Google Cloud project, enable Drive and Sheets APIs, and download `credentials.json` into `config/`.

---

### 9. Run the pipeline

```bash
poetry run python main.py
```

On the **first run**, a browser window will open asking you to authorize the app with your Google account. After authorization, a `token.json` file will be saved to `config/` and reused on subsequent runs.

---

### Performance Notes

On **macOS M2, 8 GB RAM** with the `turbo` model: ~16 audio files processed in approximately 16 minutes.

For faster processing, consider:
- Running on a machine with more RAM or a dedicated GPU
- Using a cloud VM with GPU (e.g. Google Colab, RunPod)
- Switching to Google Speech-to-Text API which offloads processing entirely and has no local memory requirements

---

## Configuration

### Environment Variables

Copy `.env.example` to `.env` inside the `config/` directory:

```bash
cp config/.env.example config/.env
```

Then fill in your OpenAI API key:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

---

### `config.py` Constants

All project configuration lives in `config/config.py`. Below is a description of each constant:

| Constant | Description |
|---|---|
| `SOURCE_FOLDER_ID` | Google Drive folder ID containing the original audio files to process |
| `SOURCE_SHEET_ID` | ID of the Google Sheet used as a template. On first run, the pipeline copies this sheet into `TARGET_PARENT_ID` and writes all results into the copy |
| `TARGET_PARENT_ID` | Google Drive folder ID where the working audio folder and the copied report sheet will be created |
| `TARGET_SHEET_NAME` | Display name for the copied report sheet created in `TARGET_PARENT_ID` |
| `TARGET_AUDIO_FOLDER_NAME` | Display name for the audio folder created inside `TARGET_PARENT_ID` |
| `WHISPER_MODEL` | Whisper model size. Default: `turbo`. See [Transcription Quality](#transcription-quality) for options |
| `WHISPER_PROMPT` | Initial context hint for Whisper to improve transcription accuracy for auto service dialogues |
| `ALLOWED_LANGUAGES` | Tuple of language codes Whisper is restricted to during detection. Default: `('uk', 'ru')` |
| `OPENAI_MODEL` | GPT model used for dialogue analysis. Default: `gpt-4o-mini`. Can be swapped for a more capable model — see [Analysis Model Quality](#analysis-model-quality) |
| `WORKS` | Full list of valid auto service work types used to classify the main work discussed in the call |
| `RESULT_OF_DIALOGUE` | List of valid call outcome types (e.g., appointment made, callback needed, transferred) |

---

## Transcription Quality

Transcription quality depends heavily on the Whisper model size and audio clarity.

The pipeline uses language detection restricted to `ALLOWED_LANGUAGES` before each transcription to prevent misdetection on ambiguous audio (e.g. mixed Ukrainian/Russian speech being misidentified as Serbian or Polish).

**Recommended model options:**

| Model | Quality | RAM | Notes |
|---|---|---|---|
| `turbo` (default) | ✅ Good | ~6 GB | Best balance of quality and speed for local use |
| `large-v3` | ✅ Best local | ~10 GB | Maximum local accuracy, slow on CPU |
| Google Speech-to-Text | ✅ Best overall | None | Superior accuracy for UK/RU, ~$0.016/min |

To switch models, change `WHISPER_MODEL` in `config/config.py`. The pipeline automatically adapts to the model's architecture — no other changes needed.

For production use with high call volumes, **Google Speech-to-Text** provides the best accuracy with no local memory requirements, at the cost of per-minute pricing.

---

## Analysis Model Quality

The GPT model used for dialogue analysis can be changed by updating `OPENAI_MODEL` in `config/config.py`. The pipeline is model-agnostic — any OpenAI-compatible model can be used.

Testing showed that **Claude Sonnet** produces significantly more detailed and accurate analysis compared to `gpt-4o-mini`, particularly for nuanced checklist evaluation and manager feedback. To integrate an alternative model, update the API client and model constant accordingly.

---

## Example Output

Below is an example of a processed call row written to Google Sheets.

> Transcribed with **Whisper turbo**, analyzed with **GPT-4o-mini**.

**Audio file:** `2024-11-13_10-09_[phone]_incoming.mp3`

**Dialogue (example):**
```
 - Доброго дня, мене звати Богдав.
 - Доброго, так. Я телегурував стосовно X5 Е70, заміна мастил. Ви могли б скинуть мені на Viber то, що ви будете заливати оригінал передній міст, задній міст, коробка і роздатка?
 - Приводи не вкинути?
 - Ні, фото мастил, який ви будете заливати.
 ...
 - Ну дивіться, я такого в принципі сенсу не бачу це зробити, я можу, але дивіться, якщо я вам надам фотографію з гугла, вона може відрізнятися від тої фотографії, від тої бляшанки, яка може переїхати до нас на наявності. Я пропоную, що ви, коли плануєте записатись, тобто всі розраховуєте націну на наші ціни, я замовляю оригінал, ви приїжджаєте, ви оглядаєте бляшанки, тобто перед тим їх залити, ви всі запчасти не зможете оглянути.
 - Я зрозумів.
 - Пів літру, так?
 - Так. Алло?
 - Так, так, пів літру три тисячі.
 - Пів літру три тисячі. Я зрозумів, ще наберу вас тоді добре. 
 - Все добре тоді, гарний дні.
```
 
**Result written to Google Sheets:**

| Field | Value                                                                                                                                                                                                                                                                                                                                                     |
|---|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Date & Time | 2024-11-13 10:09                                                                                                                                                                                                                                                                                                                                          |
| Call Type | incoming                                                                                                                                                                                                                                                                                                                                                  |
| Manager | Богдан                                                                                                                                                                                                                                                                                                                                                    |
| Greeting | ✅                                                                                                                                                                                                                                                                                                                                                         |
| Car Body | X5 E70                                                                                                                                                                                                                                                                                                                                                    |
| Car Year | 0 (Not mentioned)                                                                                                                                                                                                                                                                                                                                         |
| Mileage | 0 (Not mentioned)                                                                                                                                                                                                                                                                                                                                         |
| Diagnostics Offered | ❌                                                                                                                                                                                                                                                                                                                                                         |
| Previous Work Asked | ❌                                                                                                                                                                                                                                                                                                                                                         |
| Appointment Made | ✅                                                                                                                                                                                                                                                                                                                                                         |
| Farewell | ✅                                                                                                                                                                                                                                                                                                                                                         |
| Work Type | Заміна оливи в передньому і задньому редукторі                                                                                                                                                                                                                                                                                                            |
| Result | Інше                                                                                                                                                                                                                                                                                                                                                      |
| Spare Parts | Не обговорювалось                                                                                                                                                                                                                                                                                                                                         |
| Operation Score | **75.56 / 100**                                                                                                                                                                                                                                                                                                                                           |
| Comments | Клієнт звернувся щодо заміни мастил на BMW X5 E70 та попросив фото матеріалів у Viber. Оператор обґрунтував відмову надсилати фото з інтернету та запропонував оглянути оригінальні бляшанки на місці перед заливкою. Сильні сторони — відмінне відпрацювання заперечень та ввічливість, слабкі — розмову не завершено фінальним записом на конкретний час. |

> **Note on analysis quality:** Testing with Claude Sonnet showed significantly better analysis quality compared to GPT-4o-mini. The pipeline is model-agnostic — swapping the model requires changing a single constant in `config.py`.

---

## Troubleshooting

**`ffmpeg not found` error on first run**
Whisper requires ffmpeg to decode audio files. Install it via Homebrew on macOS (`brew install ffmpeg`) or winget on Windows (`winget install ffmpeg`), then restart your terminal.

**`SSL: CERTIFICATE_VERIFY_FAILED` on macOS**
Python installed from python.org ships without SSL certificates. Run the certificate installer for your Python version:
```bash
open /Applications/Python\ 3.x/Install\ Certificates.command
```
Replace `3.x` with your actual version (e.g. `3.12`).

**Browser doesn't open for Google OAuth**
Make sure `credentials.json` is placed in the `config/` directory and is the correct file type (OAuth 2.0 Client ID, not a Service Account key). Delete any existing `token.json` and re-run to trigger the authorization flow again.

**`token.json` expires or becomes invalid**
Delete `config/token.json` and re-run the pipeline. A new browser authorization will be triggered and a fresh token will be saved.

**No audio files found / pipeline exits immediately**
Check that `SOURCE_FOLDER_ID` points to the correct folder and that the Google account you authorized has access to it. Also verify that the source sheet (`SOURCE_SHEET_ID`) is accessible — the pipeline uses it to determine which files have already been processed.

**Transcription output looks garbled or contains wrong-language text**
This is a known Whisper limitation on low-quality or noisy audio. The pipeline restricts language detection to `ALLOWED_LANGUAGES` to reduce misdetection, but very noisy recordings may still produce poor results. Consider upgrading to `large-v3` or switching to Google Speech-to-Text for better accuracy. See [Transcription Quality](#transcription-quality).

**`mel channel mismatch` error when using `turbo` or `large-v3`**
This occurs if Whisper's mel spectrogram is generated with the wrong number of channels for the selected model. The pipeline handles this automatically via `model.dims.n_mels` — make sure you are running the latest version of the code.

**Duplicate rows appearing in Google Sheets**
If a processed row was manually deleted from the sheet, the pipeline will re-process that audio file on the next run since it uses the sheet as the source of truth for processed files. A `.txt`-based deduplication check is planned — see [Roadmap](#roadmap).

---

## Roadmap

- [ ] **Upgrade default analysis model** — replace `gpt-4o-mini` with a more capable model (e.g. Claude Sonnet) for production use.

---