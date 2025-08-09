import streamlit as st
import pandas as pd
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

# ----------------- Sidebar Login -----------------
st.set_page_config(page_title="📧 Gmail Email Viewer", layout="wide")

st.sidebar.header("🔑 Gmail Service Account Login")
uploaded_json = st.sidebar.file_uploader(
    "Upload your Gmail Service JSON file",
    type=["json"]
)

max_results = st.sidebar.slider("Number of emails to fetch", 5, 50, 10)

folder_choice = st.sidebar.selectbox(
    "Select Gmail Folder",
    ["INBOX", "DRAFT", "SPAM"]
)

# ----------------- Gmail Functions -----------------
def get_gmail_service(credentials_json):
    """Authenticate and return Gmail service, impersonating Entremotivator@gmail.com."""
    creds = service_account.Credentials.from_service_account_info(
        credentials_json,
        scopes=['https://www.googleapis.com/auth/gmail.readonly'],
        subject="Entremotivator@gmail.com"  # Force impersonation
    )
    return build('gmail', 'v1', credentials=creds)

def get_emails(service, label_ids, max_results=10):
    """Fetch emails with given label IDs."""
    results = service.users().messages().list(
        userId='me',
        labelIds=label_ids,
        maxResults=max_results
    ).execute()

    messages = results.get('messages', [])
    email_data = []

    for msg in messages:
        msg_data = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='metadata',
            metadataHeaders=['From', 'Subject', 'Date']
        ).execute()

        headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
        snippet = msg_data.get('snippet', '')

        email_data.append({
            'From': headers.get('From', ''),
            'Subject': headers.get('Subject', '(No Subject)'),
            'Date': headers.get('Date', ''),
            'Snippet': snippet
        })
    return email_data

# ----------------- Card Renderer -----------------
def render_email_cards(email_list):
    """Render emails as responsive cards."""
    if not email_list:
        st.warning("No emails found.")
        return

    cols = st.columns(2)  # Two cards per row
    col_index = 0

    for email in email_list:
        with cols[col_index]:
            st.markdown(
                f"""
                <div style="
                    background: #f8f9fa;
                    padding: 1rem;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin-bottom: 1rem;
                    ">
                    <h4 style="margin-bottom: 0.5rem;">{email['Subject']}</h4>
                    <p style="font-size: 0.9rem; color: gray;"><b>From:</b> {email['From']}</p>
                    <p style="font-size: 0.85rem; color: gray;"><b>Date:</b> {email['Date']}</p>
                    <p style="font-size: 0.9rem;">{email['Snippet']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        col_index = (col_index + 1) % 2

# ----------------- Main App -----------------
st.title("📨 Gmail Email Viewer")

if uploaded_json:
    try:
        credentials_json = json.load(uploaded_json)
        service = get_gmail_service(credentials_json)

        # Map folder names to Gmail Label IDs
        label_map = {
            "INBOX": ["INBOX"],
            "DRAFT": ["DRAFT"],
            "SPAM": ["SPAM"]
        }

        with st.spinner(f"Fetching {folder_choice.lower()} emails..."):
            emails = get_emails(service, label_map[folder_choice], max_results=max_results)
            render_email_cards(emails)

            # Optional: also show as table for quick scanning
            if st.checkbox("Show Table View"):
                df = pd.DataFrame(emails)
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                st.dataframe(df)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Please upload your Gmail service account JSON in the sidebar.")
