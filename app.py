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
        log_history(history_file, "EDIT", username, df.loc[idx])
    else:
        log_history(history_file, "DELETE", username, old_row)
        df.drop(index=idx, inplace=True)
    df.to_csv(file, index=False)

# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="Ganesh Festival App", layout="wide")

# Clear inputs BEFORE widgets are rendered
if st.session_state.get("clear_collection", False):
    st.session_state.pop("collection_name_input", None)
    st.session_state.clear_collection = False

if st.session_state.get("clear_expense", False):
    st.session_state.pop("expense_purpose_input", None)
    st.session_state.clear_expense = False

# Session State Init
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if "collection_name_input" not in st.session_state:
    st.session_state.collection_name_input = ""
if "expense_purpose_input" not in st.session_state:
    st.session_state.expense_purpose_input = ""

collections, expenses, col_history, exp_history = load_data()
total_collected = collections["Amount"].sum() if not collections.empty else 0
total_spent = expenses["Amount"].sum() if not expenses.empty else 0
balance = total_collected - total_spent

if not st.session_state.logged_in:
    st.title("🔐 GaneshKutumbam App Login")
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

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "➕ Add Collection",
    "➕ Add Expense",
    "🧾 Edit/Delete",
    "📊 View Report",
    "📜 History Logs"
])

# -------------------- Add Collection --------------------
with tab1:
    st.subheader("Add Collection")
    with st.form("add_collection_form"):
        col1, col2, col3 = st.columns(3)
        name = col1.text_input("Name", key="collection_name_input")
        amount = col2.number_input("Amount (₹)", min_value=1, key="collection_amount_input")
        date = col3.date_input("Date", key="collection_date_input")
        submitted = st.form_submit_button("Submit")
        if submitted:
            if not name.strip():
                st.error("Please enter a valid Name.")
            else:
                save_collection(name, amount, date)
                log_history(COLLECTION_HISTORY_FILE, "ADD", st.session_state.username, [name, amount, date])
                st.success(f"✅ Added collection ₹{amount} by {name}")
                st.session_state.clear_collection = True
                st.rerun()

# -------------------- Add Expense --------------------
with tab2:
    st.subheader("Add Expense")
    with st.form("add_expense_form"):
        col1, col2, col3 = st.columns(3)
        purpose = col1.text_input("Purpose", key="expense_purpose_input")
        amount = col2.number_input("Amount (₹)", min_value=1, key="expense_amount_input")
        date = col3.date_input("Date", key="expense_date_input")
        submitted = st.form_submit_button("Submit")
        if submitted:
            if not purpose.strip():
                st.error("Please enter a valid Purpose.")
            else:
                save_expense(purpose, amount, date)
                log_history(EXPENSE_HISTORY_FILE, "ADD", st.session_state.username, [purpose, amount, date])
                st.success(f"✅ Added expense ₹{amount} for {purpose}")
                st.session_state.clear_expense = True
                st.rerun()

# -------------------- Edit / Delete --------------------
with tab3:
    st.subheader("Edit or Delete Entries")
    entry_type = st.radio("Select Type", ["Collection", "Expense"], horizontal=True)
    df = collections if entry_type == "Collection" else expenses
    file = COLLECTION_FILE if entry_type == "Collection" else EXPENSE_FILE
    hist_file = COLLECTION_HISTORY_FILE if entry_type == "Collection" else EXPENSE_HISTORY_FILE

    if df.empty:
        st.warning(f"No {entry_type.lower()} records found.")
    else:
        # Editing Section
        edited_df = st.data_editor(df, num_rows="dynamic", key="editor")
        st.caption("Edit any row above. Click 'Apply Edits' to save changes.")

        if st.button("Apply Edits"):
            for i in df.index:
                try:
                    if not df.loc[i].equals(edited_df.loc[i]):
                        update_record(df.copy(), file, hist_file, i, st.session_state.username, edited_df.loc[i])
                except KeyError:
                    continue
            st.success("Changes saved successfully.")
            st.rerun()

        # Deleting Section
        df_display = df.copy()
        df_display["Index"] = df_display.index  # Preserve original index
        df_display["Select"] = False  # Add checkbox column

        edited_display = st.data_editor(
            df_display.drop(columns=["Index"]),  # Hide internal Index from view
            use_container_width=True,
            key="delete_editor",
            disabled=[col for col in df_display.columns if col not in ["Select"]],
            num_rows="dynamic"
        )

        # Re-attach Index column after edit
        edited_display["Index"] = df_display["Index"]

        selected_rows = edited_display[edited_display["Select"] == True]

        if not selected_rows.empty and st.button("Delete Selected Entries"):
            original_indices = selected_rows["Index"].tolist()

            for idx in original_indices:
                log_history(hist_file, "DELETE", st.session_state.username, df.loc[idx])
            df.drop(index=original_indices, inplace=True)
            df.to_csv(file, index=False)

            st.success(f"✅ Deleted {len(original_indices)} entr{'y' if len(original_indices) == 1 else 'ies'}.")
            st.rerun()

# -------------------- Report --------------------
with tab4:
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
with tab5:
    st.subheader("📜 History Logs")
    htype = st.selectbox("Select History Type", ["Collection", "Expense"])
    history_df = col_history if htype == "Collection" else exp_history
    if history_df.empty:
        st.info("No history records yet.")
    else:
        st.dataframe(history_df)
