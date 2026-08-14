import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

st.title("📊 Solenis CRM - Auto Entry")

# 1. Upload Excel
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.subheader("Preview Data")
    st.dataframe(df)

    # 2. Select which column has Party Name
    party_column = st.selectbox("Select column for Party Name", df.columns)

    # 3. Settings
    delay = st.slider("Delay between entries (seconds)", 1, 10, 3)
    headless = st.checkbox("Run headless (no browser window)", value=False)

    # 4. Start Automation
    if st.button("🚀 Start Automation"):
        
        # Setup browser
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        # Keep browser open if already logged in
        options.add_argument("--user-data-dir=C:\\SeleniumProfile")

        driver = webdriver.Chrome(options=options)
        
        # Navigate to the page
        driver.get("https://indiacrm.solenis.com/ebizwiz/Sales/nonwarrantyitem.aspx")
        time.sleep(3)  # Wait for page to load

        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        logs = []
        log_area = st.empty()

        success_count = 0
        fail_count = 0

        for index, row in df.iterrows():
            try:
                status_text.text(f"Processing row {index + 1} of {len(df)}...")

                # Step 1: Enter Party Name
                party_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "vpartyname"))
                )
                party_field.clear()
                party_field.send_keys(str(row[party_column]))

                # Step 2: Press Tab
                party_field.send_keys(Keys.TAB)
                time.sleep(1)

                # Step 3: Click the link
                link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, 
                        "/html/body/form/table/tbody/tr[3]/td/table/tbody/tr[2]/td[1]/a"))
                )
                link.click()
                time.sleep(delay)

                success_count += 1
                logs.append(f"✅ Row {index + 1}: {row[party_column]} - Success")

            except Exception as e:
                fail_count += 1
                logs.append(f"❌ Row {index + 1}: {row[party_column]} - Failed: {str(e)}")

            # Update progress
            progress_bar.progress((index + 1) / len(df))
            log_area.text_area("Logs", "\n".join(logs), height=200)

        driver.quit()

        # 5. Summary
        st.subheader("📋 Results")
        col1, col2 = st.columns(2)
        col1.metric("✅ Success", success_count)
        col2.metric("❌ Failed", fail_count)
        st.success("Automation complete!")