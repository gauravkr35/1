import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from fpdf import FPDF
import tempfile
import base64

# ✅ MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="AI Report Generator", layout="wide")

# ====== SAFE SESSION STATE INIT ======
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "summary_text" not in st.session_state:
    st.session_state.summary_text = ""

# ====== USER CREDENTIALS ======
users = {"admin": "demo", "gaurav": "1234"}

# ====== LOGIN FUNCTION ======
def login():
    with st.sidebar:
        st.title("🔐 Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"✅ Welcome, {username}!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

# ====== IF NOT LOGGED IN, SHOW LOGIN ======
if not st.session_state.logged_in:
    login()
    st.stop()

# ====== LOGOUT BUTTON ======
with st.sidebar:
    st.markdown(f"👋 Logged in as: `{st.session_state.username}`")
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.summary_text = ""
        st.rerun()

# ====== MAIN PAGE CONTENT ======
st.title("📊 AI Report & Chart Generator (LLaMA 3.2 via Ollama)")

# ====== FILE UPLOAD ======
uploaded_file = st.file_uploader("📂 Upload your CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.subheader("📄 Data Preview")
    st.dataframe(df.head())

    st.subheader("📊 Data Summary")
    st.write("Shape:", df.shape)
    st.write("Missing Values:", df.isnull().sum())
    st.write(df.describe())

    # ====== CHART OPTIONS ======
    st.subheader("📈 Visualize Your Data")
    chart_types = ["Scatter", "Line", "Bar", "Histogram", "Pie", "Box", "Violin", "Area"]
    chart_type = st.selectbox("Choose chart type", chart_types)

    numeric_cols = df.select_dtypes(include='number').columns.tolist()

    if chart_type != "Pie":
        x_col = st.selectbox("X-axis", df.columns)
        y_col = st.selectbox("Y-axis", numeric_cols)
    else:
        pie_labels = st.selectbox("Labels", df.columns)
        pie_values = st.selectbox("Values", numeric_cols)

    if st.button("📊 Plot Chart"):
        try:
            if chart_type == "Scatter":
                fig = px.scatter(df, x=x_col, y=y_col)
            elif chart_type == "Line":
                fig = px.line(df, x=x_col, y=y_col)
            elif chart_type == "Bar":
                fig = px.bar(df, x=x_col, y=y_col)
            elif chart_type == "Histogram":
                fig = px.histogram(df, x=x_col)
            elif chart_type == "Pie":
                fig = px.pie(df, names=pie_labels, values=pie_values)
            elif chart_type == "Box":
                fig = px.box(df, x=x_col, y=y_col)
            elif chart_type == "Violin":
                fig = px.violin(df, x=x_col, y=y_col, box=True, points="all")
            elif chart_type == "Area":
                fig = px.area(df, x=x_col, y=y_col)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"⚠️ Could not plot chart: {e}")

    # ====== AI ANALYSIS ======
    st.subheader("🧠 AI Summary (LLaMA 3.2 via Ollama)")

    if st.button("🧠 Generate AI Summary"):
        prompt = f"""
You are a data analyst. Analyze the uploaded dataset:
- Describe key trends and patterns
- Identify correlations and outliers
- Note any missing or anomalous values

Stats:
{df.describe().to_string()}
Missing:
{df.isnull().sum().to_string()}
Shape: {df.shape}
"""
        with st.spinner("🧠 Generating summary using LLaMA 3.2..."):
            try:
                response = requests.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": "llama3.2",
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    summary_text = result["message"]["content"]
                    st.session_state.summary_text = summary_text
                    st.success("✅ Summary Generated")
                    st.markdown(summary_text)
                else:
                    st.error(f"❌ Ollama Error: {response.text}")
            except Exception as e:
                st.error(f"❌ Failed to connect to Ollama: {e}")

    # ====== PDF DOWNLOAD ======
    st.subheader("📥 Download AI Summary as PDF")
    if st.session_state.summary_text:
        if st.button("📄 Generate PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="AI Report Summary", ln=True, align='C')
            pdf.multi_cell(0, 10, st.session_state.summary_text)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                pdf.output(tmp_file.name)
                with open(tmp_file.name, "rb") as f:
                    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                    href = f'<a href="data:application/pdf;base64,{base64_pdf}" download="AI_Report.pdf">📄 Click here to download your PDF report</a>'
                    st.markdown(href, unsafe_allow_html=True)
    else:
        st.info("🧠 Please generate the summary before downloading.")
