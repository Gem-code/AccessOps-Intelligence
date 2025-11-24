# AccessOps-Intelligence
AccessOps Intelligence: The Agentic Gatekeeper for Non-Human Identities

# 🚀 Front-End App Overview

This Streamlit application provides:

- 📝 Access Request Input Form
- 📊 Risk Evaluation Dashboard
- 📘 Executive Summary (AI Generated)
- 📈 Insights (Charts & Analytics)
- 📜 Request History
- 📄 Enterprise-grade PDF generation
- 🔐 Login / Access Key Gate

## AccessOps Intelligence — Local Streamlit Setup Guide

This guide explains how to run the AccessOps Intelligence Streamlit dashboard **locally on your machine**.

---

## 🚀 1. Prerequisites

Make sure the following are installed:

### **Python 3.10+**
Check version:
```bash
python --version
```

### **Pip**
```bash
pip --version
```

### **Virtual Environment (optional but recommended)**
```bash
python -m venv venv
```

Activate:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

---

## 📂 2. Project Structure

Your folder structure:

```
app/
   core/
      configs.py
      gauge.py
      markdown_cleaner.py
      pdf_generator.py
      roles.py
      state_manager.py
   ui/
      form_page.py
      history_page.py
      insights_page.py
      login.py
   main.py
   requirements.txt
history.json
README.md
```

---

## 📦 3. Install Dependencies

Run the following:

```bash
pip install -r app/requirements.txt
```

If reportlab or wkhtmltopdf errors appear, install system deps:

### Ubuntu/Debian
```bash
sudo apt-get install -y wkhtmltopdf libgl1
```

### Windows  
Install wkhtmltopdf from:  
https://wkhtmltopdf.org/downloads.html

---

## ▶️ 4. Run Streamlit Application

From the project root:

```bash
streamlit run app/main.py
```

You will see output like:

```
Local URL: http://localhost:8501
External URL: http://<your-ip>:8501
```

Open:

👉 http://localhost:8501

---

## 🔐 5. Login Screen

When the app loads:

- Enter your **ACCESS_KEY** (configured in `app/configs.py`)
- Default **ACCESS_KEY** is `demo-key`
- Click **Unlock Dashboard**

The Request Form, Insights, and History tabs will appear.

---

## 📝 6. Generate Access Request Report

1. Fill the Access Request Form  
2. Submit  
3. View:
   - Evaluation Result  
   - Gauge Chart  
   - Executive Board Report  
4. Click **Download PDF** to export a full formatted report.

---

## 📊 7. Viewing Insights

Navigate to **Insights** tab:

- Pie charts  
- Severity distribution  
- Risk score timeline  

---

## 🗂 8. Access Request History

Stored in:

```
history.json
```

Each request logs:
- Request details  
- Decision  
- Severity  
- Risk score  
- Timestamp  

---

## 🧪 9. Running in Development Mode

Enable hot reload:

```bash
streamlit run app/main.py --server.runOnSave true
```

---

## 🛠 10. Troubleshooting

### **Port already in use**
```bash
streamlit run app/main.py --server.port=8600
```

### **No module found**
Ensure you are inside your virtual environment.

### **PDF not generating**
Install wkhtmltopdf or check `pdf_generator.py`.

---

## 🎉 You're Ready!

Your AccessOps dashboard is fully running locally.  
You can now customize UI, logic, PDFs, and deploy to Cloud Run when ready.

---

## 📧 Need More Help?

Ask anytime — deployment, CI/CD, Terraform, UI upgrades, anything.


## 🧪 Testing
Run unit tests:
```bash
pytest tests/test_agents.py
```

Validates:
- Tool output schemas
- Risk score calculations  
- Gatekeeper logic
