import streamlit as st
import requests
import time
BACKEND_URL = "http://localhost:8000"  # ← Change to Railway URL for production

st.set_page_config(
    page_title="PDF Redactor",
    page_icon="Hello",
    layout="centered",
)

st.title(" Smart Document Redactor")
st.markdown("Upload PDF → Automatic PII Removal → Download Redacted Copy")
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    st.info(f" {uploaded_file.name} ({uploaded_file.size:,} bytes)")
    if st.button("Redact PII", type="primary"):
        with st.spinner("Uploading PDF..."):
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            try:
                response = requests.post(f"{BACKEND_URL}/redact", files=files, timeout=30)
                
                if response.status_code == 202:
                    job_id = response.json()["job_id"]
                    st.success(f"Job started: {job_id}")
                    status_text = st.empty()
                    progress_bar = st.progress(0)
                    
                    for attempt in range(30):
                        status = requests.get(f"{BACKEND_URL}/jobs/{job_id}", timeout=10).json()["status"]
                        status_text.info(f"Status: {status} ({attempt+1}/30)")
                        progress_bar.progress((attempt + 1) / 30)
                        
                        if status == "completed":
                            st.balloons()
                            st.success(" Redaction complete!")
                            download = requests.get(f"{BACKEND_URL}/download/{job_id}", timeout=30)
                            if download.status_code == 200:
                                st.download_button(
                                    "⬇ Download Redacted PDF",
                                    download.content,
                                    f"redacted_{uploaded_file.name}",
                                    "application/pdf",
                                    type="primary"
                                )
                                st.caption(" File auto-deleted after 5 minutes (zero retention)")
                            break
                        elif status == "failed":
                            st.error(" Redaction failed")
                            break
                        
                        time.sleep(2)
                    else:
                        st.warning(" Still processing... Check back later")
                else:
                    st.error(f"Upload failed: {response.status_code}")
            except requests.exceptions.ConnectionError:
                st.error(f"Cannot connect to backend at {BACKEND_URL}")
                st.info(" Start FastAPI server first: `uvicorn python.api.main:app --reload`")
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.markdown("---")
st.caption("Zero data retention • GDPR/HIPAA compliant • Cryptographic PII removal")