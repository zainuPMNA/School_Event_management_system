# School Event Management System 🏆🎨

A comprehensive, fully-digitized web application built with Python and Streamlit to manage school sports days and arts festivals. This system replaces chaotic paper scoring sheets and messy spreadsheets with a centralized, real-time dashboard for event coordinators and judges.

## ✨ Key Features

- **Dynamic Event Modes:** Seamlessly toggle between 'Sports' and 'Arts' modes. Event data, programs, and scores are strictly segregated while sharing core student data.
- **Bulk Data Ingestion:** Easily upload students, individual/group programs, and team assignments via CSV. The app provides downloadable CSV templates to ensure correct formatting.
- **Real-Time Score Logging:** Judges can input scores directly into the system. Includes built-in mechanisms for correcting and updating scores.
- **Live Analytics & Leaderboards:** Interactive dashboards display real-time standings for individuals and houses/teams.
- **Automated Reporting:** 
  - Generate comprehensive Winners Lists (category-wise and chronological).
  - Export data to CSV or Word Document formats.
  - Generate Coordinator Operations Checklists to track event progress.
- **Automated Certificate Generation:** Automatically generate and download printable PDF certificates for event winners.
- **Offline Capable Database:** Uses a lightweight SQLite database for fast, reliable data storage without needing a complex server setup.

## 📸 Screenshots

*(Add screenshots of your app here. Just drag and drop image files directly into this README on GitHub!)*

1. **Dashboard & Analytics:** `[Insert image of the main leaderboard]`
2. **Data Ingestion & CSV Templates:** `[Insert image of the bulk upload section]`
3. **Real-time Scoring Interface:** `[Insert image of the scoring panel]`
4. **Generated Reports/Certificates:** `[Insert image of the generated certificate or coordinator checklist]`

## 🛠️ Tech Stack

- **Frontend & App Framework:** [Streamlit](https://streamlit.io/)
- **Backend Language:** Python 3.x
- **Database:** SQLite3
- **Data Manipulation:** Pandas
- **Document Generation:** `python-docx` (Word), FPDF / ReportLab (PDFs)

## 🚀 How to Run Locally

### Prerequisites
Make sure you have [Python 3.8+](https://www.python.org/downloads/) installed on your system.

### Quick Start (Windows)
If you are on Windows, you can use the provided batch files:
1. Double-click `install.bat` to automatically set up a virtual environment and install all dependencies.
2. Double-click `start_app.bat` to launch the application in your default web browser.

### Manual Setup (All Platforms)
1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/school-event-management.git
   cd school-event-management
   ```

2. **Create a virtual environment (optional but recommended)**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Streamlit application**
   ```bash
   streamlit run app.py
   ```

The app will open automatically in your browser at `http://localhost:8501`.

## 📂 Project Structure

```text
├── app.py                # Main Streamlit application entry point
├── database.py           # SQLite database schema and connection handling
├── views/                # Streamlit UI components and page modules
│   ├── data_upload.py    # Handles CSV bulk uploads and templates
│   ├── scoring.py        # Real-time score entry interface
│   ├── dashboard.py      # Leaderboards and analytics
│   ├── downloads.py      # Certificate and report generation
│   └── ...
├── assets/               # Static assets (images, fonts, templates)
├── requirements.txt      # Python dependencies
├── install.bat           # Windows installation script
└── start_app.bat         # Windows startup script
```

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/yourusername/school-event-management/issues).

## 📝 License
This project is open-source and available under the [MIT License](LICENSE).
