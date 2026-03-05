# ============================================================
# finance_tracker.py - Complete Finance Tracker (All 3 Stages)
# ============================================================
# HOW TO RUN:
#   pip install streamlit pandas numpy openpyxl requests
#   streamlit run finance_tracker.py
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file if present
except ImportError:
    pass  # dotenv not required; set GROQ_API_KEY env var manually

# ============================================================
# CONSTANTS
# ============================================================
ALLOWED_TYPES      = ["Income", "Expense"]
ALLOWED_CATEGORIES = ["Food", "Travel", "Shopping", "Salary", "Bills"]
FILE_NAME          = "finance_data.xlsx"
GROQ_API_URL       = "https://api.groq.com/openai/v1/chat/completions"
# API key loaded from environment variable (set GROQ_API_KEY in your shell or .env)
GROQ_API_KEY       = os.environ.get("GROQ_API_KEY", "")

# ============================================================
# APP CONFIG
# ============================================================
st.set_page_config(page_title="Finance Tracker", page_icon="$", layout="wide")

# ============================================================
# SESSION STATE - remembers data between button clicks
# ============================================================
if "transactions" not in st.session_state:
    st.session_state.transactions = []
if "used_ids" not in st.session_state:
    st.session_state.used_ids = set()


# ============================================================
# STAGE 1 - HELPER FUNCTIONS
# ============================================================

def export_to_excel():
    """Save current transactions list to Excel file."""
    df = pd.DataFrame(st.session_state.transactions) if st.session_state.transactions else pd.DataFrame()
    df.to_excel(FILE_NAME, index=False)


def add_transaction(trans_id, trans_type, category, amount, date):
    """Validate and add a new transaction."""
    if not trans_id:
        return False, "Transaction ID cannot be empty."
    if trans_id in st.session_state.used_ids:
        return False, f"ID '{trans_id}' already exists! Use a unique ID."

    transaction = {
        "transaction id"  : trans_id,
        "transaction type": trans_type.upper(),
        "category"        : category.upper(),
        "amount"          : amount,
        "date"            : date.strftime("%d-%m-%Y")
    }
    st.session_state.transactions.append(transaction)
    st.session_state.used_ids.add(trans_id)
    export_to_excel()
    return True, f"Transaction '{trans_id}' added successfully!"


def view_summary():
    """Calculate and return total income, expense, and net balance."""
    total_income  = 0
    total_expense = 0
    for t in st.session_state.transactions:
        if t["transaction type"] == "INCOME":
            total_income  += t["amount"]
        else:
            total_expense += t["amount"]
    return total_income, total_expense, total_income - total_expense


def delete_by_id(del_id):
    """Delete a single transaction by its ID."""
    if del_id not in st.session_state.used_ids:
        return False, f"ID '{del_id}' not found."
    st.session_state.transactions = [
        t for t in st.session_state.transactions if t["transaction id"] != del_id
    ]
    st.session_state.used_ids.remove(del_id)
    export_to_excel()
    return True, f"Transaction '{del_id}' deleted."


def delete_all():
    """Clear all transaction data."""
    st.session_state.transactions.clear()
    st.session_state.used_ids.clear()
    export_to_excel()


# ============================================================
# STAGE 2 - OOP CLASS (TransactionManager)
# ============================================================

class TransactionManager:
    """
    Bundles all analysis functions into one class.
    OOP = related data + functions grouped together.
    """

    def __init__(self, transactions):
        self.transactions = transactions  # store data inside the object

    def get_spending_by_category(self):
        """Loop through expenses and total them per category."""
        totals = {}
        for t in self.transactions:
            if t["transaction type"] == "EXPENSE":
                cat = t["category"]
                totals[cat] = totals.get(cat, 0) + t["amount"]
        return totals

    def get_highest_expense_category(self):
        """Use np.array + np.where to find top spending category."""
        totals = self.get_spending_by_category()
        if not totals:
            return None, 0
        categories = list(totals.keys())
        amounts    = np.array(list(totals.values()))       # convert to NumPy array
        max_index  = np.where(amounts == amounts.max())[0][0]  # find index of max
        return categories[max_index], float(amounts[max_index])

    def get_unique_categories(self):
        """np.unique removes duplicates and sorts the list."""
        all_cats = [t["category"] for t in self.transactions]
        return np.unique(all_cats).tolist() if all_cats else []

    def flag_high_expenses(self, threshold=1000):
        """Use a lambda to label each row as High Expense or Normal."""
        if not self.transactions:
            return pd.DataFrame()
        df = pd.DataFrame(self.transactions)
        # Lambda = short one-line function
        flag = lambda amt, ttype: "High Expense" if (amt >= threshold and ttype == "EXPENSE") else "Normal"
        df["Flag"] = df.apply(lambda row: flag(row["amount"], row["transaction type"]), axis=1)
        return df

    def load_from_excel(self, filename):
        """Load transactions from Excel using try-except for FileNotFoundError."""
        try:
            df = pd.read_excel(filename)
            self.transactions = df.to_dict(orient="records")
            return True, len(self.transactions)
        except FileNotFoundError:
            return False, f"File '{filename}' not found."
        except Exception as e:
            return False, str(e)


# ============================================================
# STAGE 3 - LLM FUNCTIONS (Groq API)
# ============================================================

def classify_profile(total_income, total_expense):
    """Classify user profile using conditional logic (no API needed)."""
    if total_income == 0:
        return "Unknown", "Add income transactions to get your profile."
    savings_rate = (total_income - total_expense) / total_income * 100
    if savings_rate >= 30:
        return "Saver", "Excellent! You are saving well. Consider investing your surplus."
    elif savings_rate >= 10:
        return "Balanced", "Good job! Try reducing 1-2 expense categories to save more."
    else:
        return "Spender", "Your expenses are high. Review non-essential spending like Shopping and Travel."


def build_prompt(transactions, insight_type):
    """Build a text prompt from transaction data using loops + string formatting."""
    total_income    = 0
    total_expense   = 0
    category_totals = {}

    for t in transactions:
        if t["transaction type"] == "INCOME":
            total_income += t["amount"]
        else:
            total_expense += t["amount"]
            cat = t["category"]
            category_totals[cat] = category_totals.get(cat, 0) + t["amount"]

    net_balance    = total_income - total_expense
    # Build spending summary using a loop + f-strings
    spending_lines = "".join(f"  - {cat}: Rs.{amt:.2f}\n" for cat, amt in category_totals.items())

    if insight_type == "savings":
        return f"""You are a helpful financial advisor.
Total Income: Rs.{total_income:.2f} | Total Expense: Rs.{total_expense:.2f} | Balance: Rs.{net_balance:.2f}
Spending:\n{spending_lines}
Suggest a practical savings strategy in 3-4 simple sentences."""

    elif insight_type == "overspending":
        return f"""You are a financial advisor. Analyze this spending:
{spending_lines}Total Expense: Rs.{total_expense:.2f}
Identify top 2 overspending areas and suggest reductions in 3-4 sentences."""

    else:  # profile
        return f"""You are a financial coach.
Income: Rs.{total_income:.2f} | Expense: Rs.{total_expense:.2f} | Balance: Rs.{net_balance:.2f}
1. Classify user as Saver, Spender, or Balanced.
2. Give 2 short practical recommendations. Keep under 5 sentences."""


def get_financial_insights(transactions, insight_type, api_key):
    """Call Groq API and return AI insight. Uses try-except for error handling."""
    if not transactions:
        return "No transactions found. Add data in Stage 1 first."

    prompt  = build_prompt(transactions, insight_type)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model"      : "llama3-8b-8192",
        "messages"   : [{"role": "user", "content": prompt}],
        "max_tokens" : 300,
        "temperature": 0.7
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()        # raises error for 4xx / 5xx responses
        data = response.json()             # parse JSON response
        return data["choices"][0]["message"]["content"].strip()

    except requests.exceptions.HTTPError as e:
        return "Invalid API key. Please check your Groq API key." if "401" in str(e) else f"API Error: {e}"
    except KeyError:
        return "Could not read the API response. Please try again."
    except Exception as e:
        return f"Unexpected error: {e}"


# ============================================================
# ============================================================
#                   STREAMLIT UI STARTS HERE
# ============================================================
# ============================================================

# ---- SIDEBAR ----
st.sidebar.title("Finance Tracker")
st.sidebar.markdown("---")

stage = st.sidebar.radio("Go to Stage:", [
    "Stage 1 - Basic Tracker",
    "Stage 2 - Analysis",
    "Stage 3 - AI Insights"
])

st.sidebar.markdown("---")
st.sidebar.metric("Total Transactions", len(st.session_state.transactions))

if st.session_state.transactions:
    inc, exp, bal = view_summary()
    st.sidebar.metric("Income",  f"Rs.{inc:,.0f}")
    st.sidebar.metric("Expense", f"Rs.{exp:,.0f}")
    st.sidebar.metric("Balance", f"Rs.{bal:,.0f}")


# ============================================================
# STAGE 1 UI
# ============================================================
if stage == "Stage 1 - Basic Tracker":
    st.title("Stage 1: Basic Finance Tracker")
    st.caption("Add, view, summarize, and delete transactions. Data auto-saves to Excel.")
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["Add Transaction", "View All", "Summary", "Delete"])

    # --- ADD ---
    with tab1:
        st.subheader("Add a New Transaction")
        col1, col2 = st.columns(2)
        with col1:
            trans_id   = st.text_input("Transaction ID (e.g. T001)").strip().upper()
            trans_type = st.selectbox("Type", ALLOWED_TYPES)
            category   = st.selectbox("Category", ALLOWED_CATEGORIES)
        with col2:
            amount = st.number_input("Amount (Rs.)", min_value=0.01, step=50.0, format="%.2f")
            date   = st.date_input("Date")

        if st.button("Add Transaction", type="primary"):
            ok, msg = add_transaction(trans_id, trans_type, category, amount, date)
            (st.success if ok else st.error)(msg)

    # --- VIEW ALL ---
    with tab2:
        st.subheader("All Transactions")
        if not st.session_state.transactions:
            st.info("No transactions yet. Add some in the Add Transaction tab.")
        else:
            df = pd.DataFrame(st.session_state.transactions)
            st.dataframe(df, use_container_width=True, height=400)
            if len(df) > 5:
                st.subheader("Last 5 Transactions")
                st.dataframe(df.tail(5), use_container_width=True)  # .tail(5) = list slicing

    # --- SUMMARY ---
    with tab3:
        st.subheader("Financial Summary")
        if not st.session_state.transactions:
            st.info("No transactions yet.")
        else:
            inc, exp, bal = view_summary()
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Income",  f"Rs.{inc:,.2f}")
            c2.metric("Total Expense", f"Rs.{exp:,.2f}")
            c3.metric("Net Balance",   f"Rs.{bal:,.2f}", delta="Surplus" if bal >= 0 else "Deficit")

    # --- DELETE ---
    with tab4:
        st.subheader("Delete Transactions")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Delete by ID**")
            del_id = st.text_input("Enter Transaction ID to Delete").strip().upper()
            if st.button("Delete by ID"):
                if not del_id:
                    st.error("Please enter an ID.")
                else:
                    ok, msg = delete_by_id(del_id)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()

        with col2:
            st.markdown("**Delete Everything**")
            st.warning("This will remove ALL your transaction data.")
            if st.button("Delete All Transactions"):
                delete_all()
                st.success("All transactions deleted.")
                st.rerun()


# ============================================================
# STAGE 2 UI
# ============================================================
elif stage == "Stage 2 - Analysis":
    st.title("Stage 2: Spending Analysis")
    st.caption("Uses the TransactionManager OOP class and NumPy for spending analysis.")
    st.markdown("---")

    if not st.session_state.transactions:
        st.warning("No transactions found. Add some in Stage 1 first.")
    else:
        # Create a TransactionManager object from our class
        manager = TransactionManager(st.session_state.transactions)

        tab1, tab2, tab3 = st.tabs(["By Category", "Highest Expense", "Flag High Expenses"])

        # --- BY CATEGORY ---
        with tab1:
            st.subheader("Total Spending by Category")
            totals = manager.get_spending_by_category()
            if not totals:
                st.info("No EXPENSE transactions found.")
            else:
                df_cat = pd.DataFrame(list(totals.items()), columns=["Category", "Total (Rs.)"])
                df_cat = df_cat.sort_values("Total (Rs.)", ascending=False)

                col1, col2 = st.columns([1, 2])
                with col1:
                    st.dataframe(df_cat, use_container_width=True, hide_index=True)
                with col2:
                    st.bar_chart(df_cat.set_index("Category"))

                unique = manager.get_unique_categories()  # uses np.unique internally
                st.info(f"Unique categories in your data: {', '.join(unique)}")

        # --- HIGHEST EXPENSE ---
        with tab2:
            st.subheader("Highest Expense Category")
            st.caption("Uses np.array and np.where to find the top spending category.")
            top_cat, top_amt = manager.get_highest_expense_category()
            if top_cat:
                st.success(f"Highest Spending Category: {top_cat} -- Rs.{top_amt:,.2f}")
                st.markdown("**All Categories Ranked:**")
                totals = manager.get_spending_by_category()
                ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)
                for rank, (cat, amt) in enumerate(ranked, 1):
                    bar = "|" * int(amt / max(totals.values()) * 30)
                    st.text(f"#{rank}  {cat:<12}  Rs.{amt:>8,.2f}   {bar}")
            else:
                st.info("No expense data yet.")

        # --- FLAG HIGH ---
        with tab3:
            st.subheader("Flag High Expense Transactions")
            st.caption("Uses a lambda function to label transactions above a chosen threshold.")
            threshold  = st.slider("Threshold Amount (Rs.)", 100, 10000, 1000, step=100)
            df_flagged = manager.flag_high_expenses(threshold)
            if not df_flagged.empty:
                st.dataframe(df_flagged, use_container_width=True)
                count = (df_flagged["Flag"] == "High Expense").sum()
                if count:
                    st.warning(f"{count} transaction(s) exceed Rs.{threshold}.")
                else:
                    st.success(f"No transactions above Rs.{threshold}.")

    # Load from Excel
    st.markdown("---")
    st.subheader("Load from Excel")
    st.caption("Uses pd.read_excel() with try-except FileNotFoundError handling.")
    if st.button("Load finance_data.xlsx"):
        temp = TransactionManager([])
        ok, result = temp.load_from_excel(FILE_NAME)
        if ok:
            st.session_state.transactions = temp.transactions
            st.session_state.used_ids     = {t["transaction id"] for t in temp.transactions}
            st.success(f"Loaded {result} transactions from '{FILE_NAME}'.")
            st.rerun()
        else:
            st.error(f"Error: {result}")


# ============================================================
# STAGE 3 UI
# ============================================================
elif stage == "Stage 3 - AI Insights":
    st.title("Stage 3: AI-Powered Financial Insights")
    st.caption("Uses the Groq LLM API to generate personalized financial advice.")
    st.markdown("---")

    api_key = GROQ_API_KEY

    if not st.session_state.transactions:
        st.warning("No transactions found. Add some in Stage 1 first.")
    else:
        inc, exp, bal = view_summary()

        # --- Financial Profile (no API needed) ---
        st.subheader("Your Financial Profile")
        st.caption("Calculated using conditional logic -- no API call required.")
        profile, tip = classify_profile(inc, exp)

        c1, c2, c3 = st.columns(3)
        c1.metric("Income",  f"Rs.{inc:,.2f}")
        c2.metric("Expense", f"Rs.{exp:,.2f}")
        c3.metric("Balance", f"Rs.{bal:,.2f}")

        st.info(f"Profile: {profile}\n\n{tip}")

        # --- AI Insights (requires API key) ---
        st.markdown("---")
        st.subheader("Ask Groq AI")

        if not api_key:
            st.warning("API key not configured. Please contact the developer.")
        else:
            choice = st.selectbox("Choose an analysis:", [
                "1. Suggest a Savings Strategy",
                "2. Identify Overspending Areas",
                "3. Classify My Financial Profile (AI)"
            ])

            insight_map = {
                "1. Suggest a Savings Strategy"         : "savings",
                "2. Identify Overspending Areas"        : "overspending",
                "3. Classify My Financial Profile (AI)" : "profile"
            }

            if st.button("Analyse My Spending", type="primary"):
                with st.spinner("Talking to Groq AI, please wait..."):
                    result = get_financial_insights(
                        st.session_state.transactions,
                        insight_map[choice],
                        api_key
                    )

                st.success("Analysis complete!")
                st.subheader("Groq Suggests:")
                st.markdown(
                    f"""<div style="background:#1e1e2e; border-left:4px solid #7c3aed;
                    padding:16px; border-radius:8px; color:#e2e8f0;
                    font-size:15px; line-height:1.7;">
                    {result}
                    </div>""",
                    unsafe_allow_html=True
                )
                
                
                
                
                