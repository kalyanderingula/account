import streamlit as st
import pandas as pd
import os
import datetime
import json

# -------------------- Auth --------------------
def load_users():
    with open("users.json", "r") as f:
        return json.load(f)

def check_login(username, password):
    users = load_users()
    return username in users and users[username] == password

# -------------------- File Setup --------------------
COLLECTION_FILE = "data/collections.csv"
EXPENSE_FILE = "data/expenses.csv"
COLLECTION_HISTORY_FILE = "data/collections_history.csv"
EXPENSE_HISTORY_FILE = "data/expenses_history.csv"

os.makedirs("data", exist_ok=True)
file_headers = {
    COLLECTION_FILE: ["Name", "Amount", "Date"],
    EXPENSE_FILE: ["Purpose", "Amount", "Date"],
    COLLECTION_HISTORY_FILE: ["Action", "Timestamp", "Username", "Name", "Amount", "Date"],
    EXPENSE_HISTORY_FILE: ["Action", "Timestamp", "Username", "Purpose", "Amount", "Date"]
}

for file, columns in file_headers.items():
    if not os.path.exists(file):
        pd.DataFrame(columns=columns).to_csv(file, index=False)

# -------------------- Data Functions --------------------
def load_data():
    return (
        pd.read_csv(COLLECTION_FILE),
        pd.read_csv(EXPENSE_FILE),
        pd.read_csv(COLLECTION_HISTORY_FILE),
        pd.read_csv(EXPENSE_HISTORY_FILE),
    )

def save_collection(name, amount, date):
    df = pd.read_csv(COLLECTION_FILE)
    df.loc[len(df)] = [name, amount, date]
    df.to_csv(COLLECTION_FILE, index=False)

def save_expense(purpose, amount, date):
    df = pd.read_csv(EXPENSE_FILE)
    df.loc[len(df)] = [purpose, amount, date]
    df.to_csv(EXPENSE_FILE, index=False)

def log_history(file, action, username, data_row):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df = pd.read_csv(file)
    row_data = [action, timestamp, username] + list(data_row)

    if len(row_data) != len(df.columns):
        st.error(f"Mismatch between row data and file columns:\nColumns: {df.columns.tolist()}\nRow: {row_data}")
        st.stop()

    df.loc[len(df)] = row_data
    df.to_csv(file, index=False)

def update_record(df, file, history_file, idx, username, updated_row=None):
    old_row = df.loc[idx].copy()
    if updated_row is not None:
        df.loc[idx] = updated_row
        log_history(history_file, "EDIT", username, old_row)
    else:
        df.drop(index=idx, inplace=True)
        log_history(history_file, "DELETE", username, old_row)
    df.to_csv(file, index=False)

# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="Ganesh Festival App", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

collections, expenses, col_history, exp_history = load_data()
total_collected = collections["Amount"].sum() if not collections.empty else 0
total_spent = expenses["Amount"].sum() if not expenses.empty else 0
balance = total_collected - total_spent

if not st.session_state.logged_in:
    st.title("🔐 Ganesh Festival App Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if check_login(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Collected", f"₹{total_collected}")
    col2.metric("Total Spent", f"₹{total_spent}")
    col3.metric("Remaining", f"₹{balance}")
    st.stop()

st.title("🪔 ChallimamidivariPalli GaneshKutumbam ")
st.caption(f"👤 Logged in as: `{st.session_state.username}`")

tab1, tab2, tab3, tab4 = st.tabs([
    "➕ Add Entry",
    "🧾 Edit/Delete",
    "📊 View Report",
    "📜 History Logs"
])

# -------------------- Add Entry --------------------
with tab1:
    st.subheader("Add Collection / Expense")
    with st.form("add_form"):
        entry_type = st.radio("Entry Type", ["Collection", "Expense"])
        col1, col2, col3 = st.columns(3)
        name_or_purpose_label = "Name" if entry_type == "Collection" else "Purpose"
        name_or_purpose = col1.text_input(name_or_purpose_label)
        amount = col2.number_input("Amount (₹)", min_value=1)
        date = col3.date_input("Date")
        submitted = st.form_submit_button("Submit")
        if submitted:
            if not name_or_purpose.strip():
                st.error(f"Please enter a valid {name_or_purpose_label}.")
            else:
                if entry_type == "Collection":
                    save_collection(name_or_purpose, amount, date)
                    log_history(COLLECTION_HISTORY_FILE, "ADD", st.session_state.username, [name_or_purpose, amount, date])
                    st.success(f"Added collection ₹{amount} by {name_or_purpose}")
                else:
                    save_expense(name_or_purpose, amount, date)
                    log_history(EXPENSE_HISTORY_FILE, "ADD", st.session_state.username, [name_or_purpose, amount, date])
                    st.success(f"Added expense ₹{amount} for {name_or_purpose}")

# -------------------- Edit / Delete --------------------
with tab2:
    st.subheader("Edit or Delete Entries")
    entry_type = st.radio("Select Type", ["Collection", "Expense"], horizontal=True)
    df = collections if entry_type == "Collection" else expenses
    file = COLLECTION_FILE if entry_type == "Collection" else EXPENSE_FILE
    hist_file = COLLECTION_HISTORY_FILE if entry_type == "Collection" else EXPENSE_HISTORY_FILE

    if df.empty:
        st.warning(f"No {entry_type.lower()} records found.")
    else:
        edited_df = st.data_editor(df, num_rows="dynamic", key="editor")
        st.caption("Edit any row above. Click 'Apply Edits' to save changes.")

        if st.button("Apply Edits"):
            for i in df.index:
                if not df.loc[i].equals(edited_df.loc[i]):
                    update_record(df.copy(), file, hist_file, i, st.session_state.username, edited_df.loc[i])
            st.success("Changes saved successfully.")
            st.rerun()

        del_index = st.number_input("Row index to delete", min_value=0, max_value=len(df)-1, step=1)
        if st.button("Delete Entry"):
            update_record(df.copy(), file, hist_file, del_index, st.session_state.username)
            st.success(f"Deleted entry at row {del_index}")
            st.rerun()

# -------------------- Report --------------------
with tab3:
    st.subheader("📊 Financial Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Collected", f"₹{total_collected}")
    col2.metric("Total Spent", f"₹{total_spent}")
    col3.metric("Remaining", f"₹{balance}")

    st.markdown("#### Collections")
    st.dataframe(collections)

    st.markdown("#### Expenses")
    st.dataframe(expenses)

# -------------------- History --------------------
with tab4:
    st.subheader("📜 History Logs")
    htype = st.selectbox("Select History Type", ["Collection", "Expense"])
    history_df = col_history if htype == "Collection" else exp_history
    if history_df.empty:
        st.info("No history records yet.")
    else:
        st.dataframe(history_df)
