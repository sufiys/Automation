import streamlit as st
import pandas as pd
import time
from playwright.sync_api import sync_playwright

# ─── Page Config ───
st.set_page_config(page_title="CRM Auto-Fill", page_icon="🤖", layout="wide")

# ─── Custom CSS for better UI ───
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)

# ─── Header ───
st.markdown('<div class="main-header">🤖 Solenis CRM Auto-Fill</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Upload Excel → Map Columns → Auto-fill CRM Form</div>', unsafe_allow_html=True)

# ─── Session State ───
if "running" not in st.session_state:
    st.session_state.running = False
if "log" not in st.session_state:
    st.session_state.log = []
if "completed" not in st.session_state:
    st.session_state.completed = 0

# ─── Sidebar Settings ───
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("🌐 Target URL")
    target_url = st.text_input(
        "CRM URL",
        value="https://indiacrm.solenis.com/ebizwiz/Sales/nonwarrantyitem.aspx"
    )
    
    st.subheader("🦊 Firefox Profile")
    firefox_profile = st.text_input(
        "Profile Path",
        value=r"C:\Users\sufiys\AppData\Roaming\Mozilla\Firefox\Profiles\3wjnlvvx.default-esr"
    )
    
    st.subheader("⏱️ Timing")
    delay_between_rows = st.slider("Delay between rows (seconds)", 1, 10, 3)
    wait_after_tab = st.slider("Wait after Tab press (seconds)", 1, 5, 2)
    
    st.subheader("🖥️ Browser")
    headless_mode = st.checkbox("Run headless (no browser window)", value=False)

# ─── Main Content ───
tab1, tab2, tab3 = st.tabs(["📁 Upload & Map", "▶️ Run Automation", "📝 Log"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1: Upload & Map
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab1:
    st.subheader("📁 Step 1: Upload Excel File")
    
    uploaded_file = st.file_uploader(
        "Choose your Excel file",
        type=["xlsx", "xls"],
        help="Upload the Excel file containing CRM data"
    )
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.session_state.df = df
        
        st.success(f"✅ Loaded {len(df)} rows and {len(df.columns)} columns")
        
        # Data Preview
        st.subheader("👀 Data Preview")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Column Mapping
        st.subheader("🔧 Step 2: Map Columns to CRM Fields")
        
        st.markdown("""
        <div class="status-box info-box">
            Map your Excel columns to the CRM form fields below.
            Select "-- Skip --" to ignore a field.
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        columns_list = ["-- Skip --"] + list(df.columns)
        
        with col1:
            st.markdown("**CRM Form Fields**")
            party_name_col = st.selectbox("Party Name (#vpartyname)", columns_list, index=0)
            # Add more fields here as you discover them:
            # field2_col = st.selectbox("Field 2 Name", columns_list, index=0)
            # field3_col = st.selectbox("Field 3 Name", columns_list, index=0)
        
        with col2:
            st.markdown("**Mapping Summary**")
            mapping = {}
            if party_name_col != "-- Skip --":
                mapping["party_name"] = party_name_col
                st.write(f"✅ Party Name ← `{party_name_col}`")
            else:
                st.write("⏭️ Party Name — Skipped")
        
        st.session_state.mapping = mapping
        
        if mapping:
            st.success(f"✅ {len(mapping)} field(s) mapped. Go to 'Run Automation' tab.")
        else:
            st.warning("⚠️ Map at least one field to proceed.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2: Run Automation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab2:
    st.subheader("▶️ Step 3: Run Automation")
    
    if "df" not in st.session_state or "mapping" not in st.session_state:
        st.warning("⚠️ Please upload a file and map columns first (Tab 1)")
    elif not st.session_state.mapping:
        st.warning("⚠️ No columns mapped. Go back to Tab 1.")
    else:
        df = st.session_state.df
        mapping = st.session_state.mapping
        
        # Summary before running
        st.markdown(f"""
        | Setting | Value |
        |---------|-------|
        | **Rows to process** | {len(df)} |
        | **Fields mapped** | {len(mapping)} |
        | **Target URL** | {target_url} |
        | **Delay between rows** | {delay_between_rows}s |
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_btn = st.button("▶️ Start Automation", type="primary", use_container_width=True)
        with col2:
            stop_btn = st.button("⏹️ Stop", type="secondary", use_container_width=True)
        
        if stop_btn:
            st.session_state.running = False
            st.warning("⏹️ Automation stopped by user.")
        
        if start_btn:
            st.session_state.running = True
            st.session_state.log = []
            st.session_state.completed = 0
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            log_container = st.container()
            
            try:
                with sync_playwright() as p:
                    status_text.info("🚀 Launching Firefox with your profile...")
                    
                    browser = p.firefox.launch_persistent_context(
                        user_data_dir=firefox_profile,
                        headless=headless_mode
                    )
                    
                    page = browser.pages[0] if browser.pages else browser.new_page()
                    
                    for index, row in df.iterrows():
                        if not st.session_state.running:
                            break
                        
                        row_num = index + 1
                        status_text.info(f"🔄 Processing row {row_num} of {len(df)}...")
                        
                        try:
                            # Navigate to CRM page
                            page.goto(target_url, wait_until="networkidle")
                            time.sleep(1)
                            
                            # Fill Party Name
                            if "party_name" in mapping:
                                value = str(row[mapping["party_name"]])
                                page.fill("#vpartyname", value)
                                page.keyboard.press("Tab")
                                time.sleep(wait_after_tab)
                                
                                # Click the link
                                page.click("xpath=/html/body/form/table/tbody/tr[3]/td/table/tbody/tr[2]/td[1]/a")
                                time.sleep(2)
                            
                            # Log success
                            st.session_state.log.append({"row": row_num, "status": "✅ Success", "detail": f"Party: {value}"})
                            
                        except Exception as e:
                            st.session_state.log.append({"row": row_num, "status": "❌ Failed", "detail": str(e)})
                        
                        # Update progress
                        st.session_state.completed = row_num
                        progress_bar.progress(row_num / len(df))
                        
                        # Delay between rows
                        time.sleep(delay_between_rows)
                    
                    browser.close()
                
                status_text.success(f"🎉 Done! Processed {st.session_state.completed}/{len(df)} rows.")
                
            except Exception as e:
                st.error(f"❌ Browser Error: {str(e)}")
            
            st.session_state.running = False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3: Log
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab3:
    st.subheader("📝 Execution Log")
    
    if st.session_state.log:
        log_df = pd.DataFrame(st.session_state.log)
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        total = len(log_df)
        success = len(log_df[log_df["status"].str.contains("Success")])
        failed = total - success
        
        col1.metric("Total Processed", total)
        col2.metric("✅ Success", success)
        col3.metric("❌ Failed", failed)
        
        # Full log table
        st.dataframe(log_df, use_container_width=True)
        
        # Download log
        csv = log_df.to_csv(index=False)
        st.download_button("📥 Download Log (CSV)", csv, "automation_log.csv", "text/csv")
    else:
        st.info("No log entries yet. Run the automation first.")

