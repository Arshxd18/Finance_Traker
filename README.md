# 💰 Finance Tracker Application

A **Python + Streamlit** finance tracking application built across 3 stages — covering basic CRUD operations, OOP-based analysis, and AI-powered financial insights using the **Groq LLM API**.

---

## 🚀 Features

### Stage 1 — Basic Tracker
- Add, view, and delete transactions
- Supports **Income** & **Expense** types
- Categories: Food, Travel, Shopping, Salary, Bills
- Auto-saves all data to **Excel** (`finance_data.xlsx`)
- Prevents duplicate Transaction IDs
- View a live **financial summary** (Income, Expense, Net Balance)

### Stage 2 — Spending Analysis (OOP + NumPy)
- **OOP Class** (`TransactionManager`) for structured analysis
- Spending broken down by category using loops + dictionaries
- Highest expense category detected using **NumPy** (`np.array`, `np.where`)
- Unique categories extracted with `np.unique`
- High-expense transactions flagged with a **lambda function**
- Load transactions back from Excel with `try-except` error handling

### Stage 3 — AI-Powered Insights (Groq API)
- Classify financial profile: **Saver**, **Balanced**, or **Spender**
- Ask Groq AI for:
  - 💡 Savings strategy suggestions
  - 📊 Overspending area identification
  - 🧠 AI-based financial profile classification
- Dynamic prompt builder using loops and f-strings
- API calls handled with full `try-except` error handling

---

## 🛠️ Tech Stack

| Tool        | Purpose                         |
|-------------|----------------------------------|
| Python 3.x  | Core language                    |
| Streamlit   | Web UI framework                 |
| Pandas      | Data manipulation & Excel I/O    |
| NumPy       | Numerical analysis               |
| Requests    | Groq API HTTP calls              |
| OpenPyXL    | Excel file read/write support    |
| Groq API    | LLM-powered financial insights   |

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Arshxd18/Finance_Traker.git
cd Finance_Traker
```

### 2. Install Dependencies
```bash
pip install streamlit pandas numpy openpyxl requests
```

### 3. Run the App
```bash
streamlit run financetrakerapplication.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## 📁 Project Structure

```
Finance_Traker/
│
├── financetrakerapplication.py   # Main application (all 3 stages)
├── finance_data.xlsx             # Auto-generated data file (created on first use)
└── README.md                     # Project documentation
```

---

## 🧠 Key Python Concepts Demonstrated

| Concept              | Where Used                                      |
|----------------------|-------------------------------------------------|
| Lists & Dicts        | Transaction storage and summaries               |
| Functions            | `add_transaction`, `delete_by_id`, `view_summary` |
| OOP / Classes        | `TransactionManager` class (Stage 2)            |
| NumPy Arrays         | `np.array`, `np.where`, `np.unique` (Stage 2)  |
| Lambda Functions     | High-expense flagging (Stage 2)                 |
| Try-Except           | File I/O and API error handling                 |
| API Integration      | Groq LLM API calls (Stage 3)                    |
| Streamlit Session    | `st.session_state` for persistent data          |
| Pandas DataFrames    | Data display and Excel export                   |
| String Formatting    | F-strings and dynamic prompt building           |

---

## 📸 App Preview

> **Sidebar** — Navigate between the 3 stages with live balance metrics  
> **Stage 1** — Clean tabbed interface for adding/viewing/deleting transactions  
> **Stage 2** — Bar charts, ranked expense tables, and flagged high spends  
> **Stage 3** — AI-generated financial advice in a styled result card

---

## 👤 Author

**Mohamed Arshad**  
NIIT — Basic Python Project  
[GitHub: @Arshxd18](https://github.com/Arshxd18)

---

## 📄 License

This project is for educational purposes as part of the NIIT Python curriculum.
