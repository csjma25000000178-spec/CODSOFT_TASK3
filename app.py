
import json
import tempfile
from pathlib import Path

import streamlit as st
from scanner import scan_python_file

st.set_page_config(
    page_title="CodeShield | Secure Code Assessment",
    page_icon="🛡️",
    layout="wide",
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #06101f, #08172a 55%, #04101d);
    color: #e6f4ff;
}
[data-testid="stHeader"] {
    background: rgba(5,16,31,.95);
}
[data-testid="stSidebar"] {
    background: #09172b;
    border-right: 1px solid #183653;
}
.block-container {
    max-width: 1450px;
    padding-top: 2rem;
}
h1,h2,h3 {
    color: #f2f8ff !important;
}
p,label {
    color: #a9c9e5;
}
[data-testid="stMetric"] {
    background: linear-gradient(145deg,#10243a,#0a1b2e);
    border: 1px solid #1c3c58;
    padding: 20px;
    border-radius: 15px;
}
[data-testid="stMetricValue"] {
    color: white;
}
[data-testid="stMetricLabel"] {
    color: #70dce8;
}
.stButton > button,
.stDownloadButton > button {
    background: #00d7bd;
    color: #041522;
    border: 0;
    border-radius: 9px;
    min-height: 43px;
    font-weight: 700;
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    background: #62f4df;
    color: #041522;
}
[data-testid="stFileUploader"] {
    background: #0b2035;
    border: 1px dashed #168eaa;
    padding: 15px;
    border-radius: 12px;
}
[data-testid="stExpander"] {
    border: 1px solid #1c3c58;
    border-radius: 10px;
    background: #0a1a2b;
}
hr {
    border-color: #1c3c58;
}
.cs-brand {
    color: #00e4cc;
    font-size: 27px;
    font-weight: 800;
}
.cs-subtitle {
    color: #91b7d4;
    font-size: 11px;
    letter-spacing: 2px;
}
.cs-banner {
    background: linear-gradient(110deg,#102943,#092034);
    border: 1px solid #1b4961;
    border-radius: 16px;
    padding: 23px;
    margin: 12px 0 22px;
}
</style>
""", unsafe_allow_html=True)

# Sidebar: branding and information only
with st.sidebar:
    st.markdown(
        '<div class="cs-brand">🛡️ CodeShield</div>'
        '<div class="cs-subtitle">SECURE CODE ASSESSMENT</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown("### ◈ Security Dashboard")
    st.caption("Python source code analysis")
    st.caption("Powered by Bandit")
    st.divider()
    st.markdown("**Workflow**")
    st.write("01  Upload source code")
    st.write("02  Run security scan")
    st.write("03  Review findings")
    st.write("04  Download report")
    st.divider()
    st.caption("SCAN  •  DETECT  •  SECURE")

# Main dashboard: all content on one page
st.markdown(
    '<div class="cs-banner">'
    '<h1>Welcome to <span style="color:#00e4cc">'
    'CodeShield</span></h1>'
    '<p>Analyze your code. Find security issues. '
    'Build safer applications.</p>'
    '</div>',
    unsafe_allow_html=True,
)

st.info(
    "Only scan code you own or are authorized to assess. "
    "Uploaded source code is analyzed, not executed by this dashboard. "
    "A clean scan does not guarantee complete security."
)

st.subheader("⌘  Scan Your Python Code")

uploaded_file = st.file_uploader(
    "Upload a Python source file (.py)",
    type=["py"],
    key="source_upload",
)

if uploaded_file:
    st.success(f"Selected file: {uploaded_file.name}")
else:
    st.caption("Choose a .py file to enable the scan.")

run_clicked = st.button(
    "▶  Run Security Scan",
    use_container_width=True,
    disabled=uploaded_file is None,
)

if run_clicked and uploaded_file is not None:
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=".py",
            delete=False,
        ) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_path = Path(temp_file.name)

        with st.spinner("Analyzing source code with Bandit..."):
            report = scan_python_file(temp_path)

        report["scanned_file"] = uploaded_file.name
        st.session_state["last_report"] = report
        st.success("Security scan completed successfully!")

    except Exception as error:
        st.error(f"Scan failed: {error}")

    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

# Results remain visible after Streamlit reruns
report = st.session_state.get("last_report")

st.divider()
st.subheader("◈  Security Assessment Results")

if report:
    issues = report["issues"]

    high = sum(i["severity"].upper() == "HIGH" for i in issues)
    medium = sum(i["severity"].upper() == "MEDIUM" for i in issues)
    low = sum(i["severity"].upper() == "LOW" for i in issues)

    st.caption(f"Scanned file: {report['scanned_file']}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Findings", len(issues))
    c2.metric("High Severity", high)
    c3.metric("Medium Severity", medium)
    c4.metric("Low Severity", low)

    if not issues:
        st.success(
            "Bandit reported no findings in this scan. "
            "This does not guarantee that the code is secure."
        )
    else:
        tabs = st.tabs([
            f"All ({len(issues)})",
            f"High ({high})",
            f"Medium ({medium})",
            f"Low ({low})",
        ])

        filtered_lists = [
            issues,
            [i for i in issues if i["severity"].upper() == "HIGH"],
            [i for i in issues if i["severity"].upper() == "MEDIUM"],
            [i for i in issues if i["severity"].upper() == "LOW"],
        ]

        for tab, filtered in zip(tabs, filtered_lists):
            with tab:
                if not filtered:
                    st.caption("No findings in this category.")

                for issue in filtered:
                    heading = (
                        f"{issue['severity']}  |  "
                        f"{issue['test_id']}  |  "
                        f"Line {issue['line']}"
                    )

                    with st.expander(heading):
                        st.write("**Finding:**", issue["issue"])
                        st.write(
                            "**Confidence:**",
                            issue["confidence"],
                        )

                        if issue.get("code"):
                            st.code(issue["code"], language="python")

                        cwe = issue.get("cwe", {})
                        if isinstance(cwe, dict) and cwe.get("id"):
                            st.write("**CWE:**", cwe["id"])

                        st.write(
                            "**Recommended action:**",
                            issue["recommendation"],
                        )

    st.divider()
    st.subheader("▤  Export Security Report")

    st.download_button(
        "⬇  Download JSON Report",
        data=json.dumps(report, indent=4),
        file_name="codeshield_report.json",
        mime="application/json",
        use_container_width=True,
    )

else:
    st.info(
        "No scan results yet. Upload sample_vulnerable.py above "
        "and click Run Security Scan to see the findings here."
    )

st.divider()
st.subheader("ⓘ  About CodeShield")
st.write(
    "CodeShield is an educational Python secure-code assessment "
    "dashboard using Bandit static analysis. Findings require human "
    "review, and automated scanning cannot detect every vulnerability."
)

st.caption(
    "CodeShield | Secure Code Assessment | Educational use"
)
