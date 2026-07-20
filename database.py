import streamlit as st
from supabase import create_client

@st.cache_resource
def get_db_connection():
    # Wir holen die Daten direkt aus den Streamlit Secrets und übergeben sie an create_client
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_db_connection()