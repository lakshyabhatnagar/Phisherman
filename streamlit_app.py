import os
from html import escape
from urllib.parse import urlparse

import requests
import streamlit as st
from dotenv import load_dotenv

from networksecurity.constants.training_pipeline import FEATURE_COLUMNS


load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

FEATURE_HELP = {
    "having_IP_Address": ("IP address in URL", "Checks whether the URL uses a raw IP instead of a domain."),
    "URL_Length": ("URL length", "Longer URLs are often used to hide suspicious paths."),
    "Shortining_Service": ("URL shortener", "Flags shortened links from services like bit.ly or tinyurl."),
    "having_At_Symbol": ("At symbol", "URLs with @ can hide the real destination."),
    "double_slash_redirecting": ("Double slash redirect", "Extra // after the protocol can indicate redirection tricks."),
    "Prefix_Suffix": ("Dash in domain", "Hyphens in domains can be a phishing signal."),
    "having_Sub_Domain": ("Subdomain depth", "Many subdomains can make a fake domain look official."),
    "SSLfinal_State": ("SSL status", "Captures whether HTTPS/SSL looks valid or suspicious."),
    "Domain_registeration_length": ("Domain registration", "Short-lived domains are more likely to be risky."),
    "Favicon": ("Favicon source", "Checks whether the page icon comes from the same domain."),
    "port": ("Port usage", "Unusual open ports can be suspicious."),
    "HTTPS_token": ("HTTPS token in domain", "Attackers sometimes put 'https' inside the domain text."),
    "Request_URL": ("External objects", "Measures whether images/scripts load from outside domains."),
    "URL_of_Anchor": ("Anchor URLs", "Checks whether links point away from the current domain."),
    "Links_in_tags": ("Links in tags", "Looks at external links inside meta/script/link tags."),
    "SFH": ("Form handler", "Checks whether form submission goes to a risky target."),
    "Submitting_to_email": ("Email submission", "Flags forms that submit data through email."),
    "Abnormal_URL": ("Abnormal URL", "Compares the URL against expected domain identity."),
    "Redirect": ("Redirect count", "Too many redirects can indicate hiding behavior."),
    "on_mouseover": ("Mouseover script", "Checks whether hover behavior changes the visible URL."),
    "RightClick": ("Right-click blocking", "Some phishing pages disable right-click inspection."),
    "popUpWidnow": ("Popup window", "Flags pages that trigger popup windows."),
    "Iframe": ("Iframe usage", "Hidden iframes can be used to mask content."),
    "age_of_domain": ("Domain age", "Newer domains are less trustworthy."),
    "DNSRecord": ("DNS record", "Missing or unusual DNS records can be suspicious."),
    "web_traffic": ("Web traffic", "Low or missing traffic can indicate a throwaway site."),
    "Page_Rank": ("Page rank", "Low reputation score can increase risk."),
    "Google_Index": ("Google indexed", "Unindexed pages can be less trustworthy."),
    "Links_pointing_to_page": ("Inbound links", "Few backlinks can indicate low reputation."),
    "Statistical_report": ("Blacklist report", "Checks whether the URL matches known suspicious patterns."),
}

USER_FIELDS = [
    "having_IP_Address",
    "URL_Length",
    "Shortining_Service",
    "having_At_Symbol",
    "double_slash_redirecting",
    "SSLfinal_State",
    "Prefix_Suffix",
    "having_Sub_Domain",
    "port",
    "HTTPS_token",
]

INTERNAL_FIELDS = [field for field in FEATURE_COLUMNS if field not in USER_FIELDS]

FIELD_OPTIONS = {
    "having_IP_Address": {
        "Auto default": None,
        "Yes, URL uses an IP address": -1,
        "No, URL uses a normal domain": 1,
    },
    "URL_Length": {
        "Auto default": None,
        "Short or normal URL": 1,
        "Medium length URL": 0,
        "Very long URL": -1,
    },
    "Shortining_Service": {
        "Auto default": None,
        "Yes, URL shortener is used": -1,
        "No, full domain is visible": 1,
    },
    "having_At_Symbol": {
        "Auto default": None,
        "Yes, @ symbol appears in URL": -1,
        "No @ symbol in URL": 1,
    },
    "double_slash_redirecting": {
        "Auto default": None,
        "Yes, extra // appears after the protocol": -1,
        "No extra // redirect pattern": 1,
    },
    "Prefix_Suffix": {
        "Auto default": None,
        "Yes, domain contains a hyphen": -1,
        "No hyphen in domain": 1,
    },
    "having_Sub_Domain": {
        "Auto default": None,
        "No extra subdomain": 1,
        "One extra subdomain": 0,
        "Many subdomains": -1,
    },
    "SSLfinal_State": {
        "Auto default": None,
        "HTTPS with valid-looking SSL": 1,
        "SSL state unknown": 0,
        "No HTTPS or SSL looks invalid": -1,
    },
    "port": {
        "Auto default": None,
        "Normal web port": 1,
        "Unusual port in URL": -1,
    },
    "HTTPS_token": {
        "Auto default": None,
        "Domain text contains 'https'": -1,
        "Domain text does not contain 'https'": 1,
    },
}


def inject_styles():
    st.markdown(
        """
        <style>
        :root {
            --bg: #080a09;
            --panel: rgba(18, 22, 19, 0.86);
            --panel-strong: rgba(24, 29, 25, 0.94);
            --line: rgba(240, 247, 238, 0.12);
            --text: #f4f7f2;
            --muted: rgba(244, 247, 242, 0.62);
            --teal: #2dd4bf;
            --teal-dark: #0f766e;
            --amber: #f59e0b;
            --red: #ef4444;
        }
        [data-testid="stAppViewContainer"] {
            background:
                linear-gradient(180deg, rgba(45, 212, 191, 0.08), transparent 380px),
                linear-gradient(90deg, rgba(245, 158, 11, 0.04), transparent 44%),
                var(--bg);
        }
        [data-testid="stAppViewContainer"]::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background-image:
                linear-gradient(rgba(244, 247, 242, 0.045) 1px, transparent 1px),
                linear-gradient(90deg, rgba(244, 247, 242, 0.035) 1px, transparent 1px);
            background-size: 44px 44px;
            mask-image: linear-gradient(to bottom, black, transparent 78%);
        }
        [data-testid="stHeader"] {
            background: transparent;
        }
        [data-testid="stSidebar"] {
            background: #0b0e0c;
            border-right: 1px solid var(--line);
        }
        .block-container {
            max-width: 1120px;
            padding-top: 2.5rem;
            padding-bottom: 3rem;
        }
        h1, h2, h3, p, label, span {
            letter-spacing: 0;
        }
        h1, h2, h3 {
            color: var(--text);
        }
        h1 {
            font-size: 3.6rem !important;
            line-height: 1;
            margin-bottom: 0.35rem !important;
        }
        h2, h3 {
            margin-top: 0.25rem !important;
        }
        div[data-testid="stCaptionContainer"] {
            color: var(--muted);
            font-size: 0.82rem;
            line-height: 1.35;
        }
        .hero-shell {
            display: grid;
            grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.65fr);
            gap: 1rem;
            align-items: stretch;
            margin: 0.25rem 0 1.35rem;
        }
        .hero-copy {
            border: 1px solid var(--line);
            border-radius: 28px;
            padding: 1.55rem 1.65rem;
            background:
                linear-gradient(135deg, rgba(45, 212, 191, 0.12), rgba(245, 158, 11, 0.05)),
                var(--panel);
            box-shadow: 0 26px 80px rgba(0, 0, 0, 0.34);
        }
        .eyebrow {
            color: var(--teal);
            font-size: 0.78rem;
            font-weight: 900;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin-bottom: 0.7rem;
        }
        .hero-copy p {
            color: var(--muted);
            margin: 0.7rem 0 0;
            max-width: 680px;
            font-size: 1.02rem;
            line-height: 1.7;
        }
        .hero-panel {
            border: 1px solid var(--line);
            border-radius: 28px;
            padding: 1.2rem;
            background: var(--panel-strong);
        }
        .status-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-bottom: 1rem;
        }
        .status-chip,
        .preview-chip {
            display: inline-flex;
            align-items: center;
            min-height: 32px;
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 0.35rem 0.72rem;
            color: var(--text);
            background: rgba(255, 255, 255, 0.05);
            font-size: 0.82rem;
            font-weight: 800;
        }
        .status-ok,
        .preview-safe {
            border-color: rgba(45, 212, 191, 0.45);
            color: #99f6e4;
            background: rgba(45, 212, 191, 0.1);
        }
        .status-bad,
        .preview-warn {
            border-color: rgba(245, 158, 11, 0.5);
            color: #fed7aa;
            background: rgba(245, 158, 11, 0.11);
        }
        .hero-number {
            color: var(--text);
            font-size: 3.4rem;
            line-height: 1;
            font-weight: 950;
        }
        .hero-note {
            color: var(--muted);
            margin-top: 0.35rem;
        }
        .signal-bars {
            display: grid;
            gap: 0.55rem;
            margin-top: 1.2rem;
        }
        .signal-bars span {
            display: block;
            height: 8px;
            border-radius: 999px;
            background: linear-gradient(90deg, var(--teal), transparent);
        }
        .signal-bars span:nth-child(2) {
            width: 76%;
            background: linear-gradient(90deg, var(--amber), transparent);
        }
        .signal-bars span:nth-child(3) {
            width: 52%;
            background: linear-gradient(90deg, #94a3b8, transparent);
        }
        div[data-testid="stForm"] {
            border: 1px solid var(--line);
            border-radius: 24px;
            padding: 1.05rem 1.15rem 1.2rem;
            background: var(--panel);
            box-shadow: 0 20px 70px rgba(0, 0, 0, 0.24);
        }
        div[data-baseweb="input"],
        div[data-baseweb="select"] > div {
            min-height: 42px;
            border-radius: 12px !important;
            background: rgba(255, 255, 255, 0.065) !important;
            border: 1px solid rgba(244, 247, 242, 0.11) !important;
            box-shadow: none !important;
        }
        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="select"] > div:focus-within {
            border-color: rgba(45, 212, 191, 0.58) !important;
            box-shadow: 0 0 0 3px rgba(45, 212, 191, 0.12) !important;
        }
        div[data-baseweb="input"] input {
            font-weight: 760;
            color: var(--text);
            font-size: 0.95rem;
        }
        div[data-baseweb="select"] span {
            font-weight: 760;
            font-size: 0.95rem;
        }
        div[data-testid="stSelectbox"] {
            margin-bottom: -0.2rem;
        }
        div.stButton > button {
            width: 100%;
            border-radius: 999px;
            border: 0;
            min-height: 48px;
            padding: 0.78rem 1rem;
            font-weight: 850;
            background: linear-gradient(135deg, #0f766e, #14b8a6);
            color: white;
            box-shadow: 0 14px 34px rgba(20, 184, 166, 0.22);
        }
        div[data-testid="stFormSubmitButton"] button {
            width: 100%;
            border-radius: 999px;
            border: 0;
            min-height: 48px;
            padding: 0.78rem 1rem;
            font-weight: 850;
            background: linear-gradient(135deg, #0f766e, #14b8a6);
            color: white;
            box-shadow: 0 14px 34px rgba(20, 184, 166, 0.22);
        }
        div.stButton > button:hover,
        div[data-testid="stFormSubmitButton"] button:hover {
            filter: brightness(1.06);
            color: white;
            border: 0;
        }
        .section-head {
            margin: 0.15rem 0 0.85rem;
        }
        .section-head h2 {
            margin: 0 !important;
            font-size: 1.65rem;
        }
        .section-head p {
            margin: 0.35rem 0 0;
            color: var(--muted);
            line-height: 1.55;
        }
        .url-preview {
            display: flex;
            gap: 0.45rem;
            flex-wrap: wrap;
            margin: 0.85rem 0 0.25rem;
        }
        .internal-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.65rem;
            margin-top: 0.35rem;
        }
        .field-chip {
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 0.75rem 0.85rem;
            background: rgba(255, 255, 255, 0.045);
        }
        .field-chip strong {
            display: block;
            color: var(--text);
            font-size: 0.88rem;
            margin-bottom: 0.25rem;
        }
        .field-chip span {
            color: var(--muted);
            font-size: 0.82rem;
            line-height: 1.35;
        }
        .manual-note {
            color: var(--muted);
            min-height: 48px;
            display: flex;
            align-items: center;
            line-height: 1.4;
        }
        .result-card {
            border-radius: 28px;
            padding: 1.45rem;
            margin-top: 1.15rem;
            color: #f8fafc;
            overflow: hidden;
            position: relative;
            isolation: isolate;
        }
        .result-card::before {
            content: "";
            position: absolute;
            inset: 0;
            opacity: 0.16;
            background-image: linear-gradient(135deg, rgba(255, 255, 255, 0.44) 0 1px, transparent 1px);
            background-size: 18px 18px;
            pointer-events: none;
            z-index: -1;
        }
        .result-safe {
            border: 1px solid rgba(45, 212, 191, 0.45);
            background: linear-gradient(135deg, #052e2b 0%, #0f766e 100%);
            box-shadow: 0 0 30px rgba(45, 212, 191, 0.28);
        }
        .result-moderate {
            border: 1px solid rgba(251, 191, 36, 0.5);
            background: linear-gradient(135deg, #451a03 0%, #b45309 100%);
            box-shadow: 0 0 30px rgba(251, 191, 36, 0.25);
        }
        .result-danger {
            border: 1px solid rgba(248, 113, 113, 0.5);
            background: linear-gradient(135deg, #450a0a 0%, #b91c1c 100%);
            box-shadow: 0 0 30px rgba(248, 113, 113, 0.25);
        }
        .result-topline {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            position: relative;
        }
        .risk-pill {
            border: 1px solid rgba(255, 255, 255, 0.28);
            border-radius: 999px;
            padding: 0.28rem 0.72rem;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            background: rgba(255, 255, 255, 0.12);
            white-space: nowrap;
        }
        .result-label {
            font-size: 2.15rem;
            font-weight: 800;
            margin: 0.4rem 0 0.2rem 0;
            color: #ffffff;
            position: relative;
        }
        .result-copy {
            color: rgba(255, 255, 255, 0.78);
            font-size: 0.98rem;
            margin: 0 0 1rem 0;
            position: relative;
        }
        .result-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.7rem;
            position: relative;
        }
        .result-stat {
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 14px;
            padding: 0.75rem 0.85rem;
            background: rgba(15, 23, 42, 0.22);
        }
        .result-stat-label {
            color: rgba(255, 255, 255, 0.68);
            font-size: 0.78rem;
            margin-bottom: 0.25rem;
        }
        .result-stat-value {
            color: #ffffff;
            font-size: 1rem;
            font-weight: 800;
        }
        .confidence-track {
            height: 10px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.18);
            overflow: hidden;
            margin: 1.05rem 0 0.15rem;
            position: relative;
        }
        .confidence-fill {
            height: 100%;
            border-radius: 999px;
        }
        .fill-safe {
            background: #5eead4;
        }
        .fill-moderate {
            background: #fbbf24;
        }
        .fill-danger {
            background: #f87171;
        }
        div[data-baseweb="tab-list"] {
            gap: 0.5rem;
            border-bottom: 1px solid var(--line);
        }
        button[data-baseweb="tab"] {
            border-radius: 999px 999px 0 0;
            padding-left: 1rem;
            padding-right: 1rem;
            font-weight: 850;
        }
        @media (max-width: 800px) {
            .block-container {
                padding-top: 1.25rem;
            }
            h1 {
                font-size: 2.55rem !important;
            }
            .hero-shell {
                grid-template-columns: 1fr;
            }
            .hero-copy,
            .hero-panel,
            div[data-testid="stForm"] {
                border-radius: 20px;
            }
            .result-grid,
            .manual-fields {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .internal-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=10, show_spinner=False)
def api_is_live(api_url):
    try:
        return requests.get(f"{api_url}/health", timeout=2).ok
    except requests.RequestException:
        return False


def render_hero(api_url):
    live = api_is_live(api_url)
    status_class = "status-ok" if live else "status-bad"
    status_text = "API online" if live else "API offline"
    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="hero-copy">
                <div class="eyebrow">Phisherman</div>
                <h1>Scan the link. Keep the signal.</h1>
                <p>Clean URL risk checks backed by reputation data, saved model artifacts, and drift-aware predictions.</p>
            </div>
            <div class="hero-panel">
                <div class="status-row">
                    <span class="status-chip {status_class}">{status_text}</span>
                    <span class="status-chip">Safe Browsing</span>
                    <span class="status-chip">GCS models</span>
                </div>
                <div class="hero-number">30</div>
                <div class="hero-note">signals behind each prediction</div>
                <div class="signal-bars">
                    <span style="width: 92%"></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section(title, copy):
    st.markdown(
        f"""
        <div class="section-head">
            <h2>{escape(title)}</h2>
            <p>{escape(copy)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def parse_url_preview(url):
    cleaned = url.strip()
    if not cleaned:
        return None
    target = cleaned if "://" in cleaned else f"https://{cleaned}"
    parsed = urlparse(target)
    if not parsed.netloc:
        return None
    try:
        port = parsed.port
    except ValueError:
        port = "invalid"
    return {
        "scheme": parsed.scheme.upper(),
        "host": parsed.hostname or parsed.netloc,
        "port": port or ("443" if parsed.scheme == "https" else "80"),
        "path_length": len(parsed.path or ""),
    }


def render_url_preview(url):
    preview = parse_url_preview(url)
    if not preview:
        return
    scheme_class = "preview-safe" if preview["scheme"] == "HTTPS" else "preview-warn"
    st.markdown(
        f"""
        <div class="url-preview">
            <span class="preview-chip {scheme_class}">{escape(str(preview["scheme"]))}</span>
            <span class="preview-chip">{escape(str(preview["host"]))}</span>
            <span class="preview-chip">Port {escape(str(preview["port"]))}</span>
            <span class="preview-chip">Path {preview["path_length"]} chars</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def select_feature(field):
    title, description = FEATURE_HELP[field]
    options = FIELD_OPTIONS[field]
    choice = st.selectbox(title, list(options), key=field, help=description)
    st.caption(description)
    return options[choice]


def collect_fields(fields, columns=2):
    payload = {}
    cols = st.columns(columns)
    for index, field in enumerate(fields):
        with cols[index % columns]:
            value = select_feature(field)
            if value is not None:
                payload[field] = value
    return payload


def risk_theme(result):
    confidence = result.get("confidence") or 0
    is_safe = result["label"].lower() == "legitimate"
    if confidence < 0.7:
        return "result-moderate", "Moderate risk", "Model confidence is not strong. Add more fields for a better read."
    if is_safe:
        return "result-safe", "Safe URL", "The supplied signals look low risk."
    return "result-danger", "High risk", "The supplied signals look suspicious."


def result_card(result):
    confidence = result.get("confidence")
    confidence_text = f"{confidence:.1%}" if confidence is not None else "Not available"
    confidence_width = round(max(0, min(confidence or 0, 1)) * 100, 1)
    drift = result["drift"]
    theme, headline, summary = risk_theme(result)
    fill_class = theme.replace("result-", "fill-")
    drift_text = "Yes" if drift["exceeded"] else "No"
    retrain_text = "Yes" if result["retraining_triggered"] else "No"
    st.markdown(
        f"""
        <div class="result-card {theme}">
            <div class="result-topline">
                <div class="risk-pill">Prediction</div>
                <div class="risk-pill">{escape(result["label"].title())}</div>
            </div>
            <div class="result-label">{escape(headline)}</div>
            <p class="result-copy">{escape(summary)}</p>
            <div class="confidence-track">
                <div class="confidence-fill {fill_class}" style="width: {confidence_width}%"></div>
            </div>
            <div class="result-grid">
                <div class="result-stat">
                    <div class="result-stat-label">Confidence</div>
                    <div class="result-stat-value">{confidence_text}</div>
                </div>
                <div class="result-stat">
                    <div class="result-stat-label">Defaults used</div>
                    <div class="result-stat-value">{len(result.get("defaulted_fields", []))}</div>
                </div>
                <div class="result-stat">
                    <div class="result-stat-label">Drift exceeded</div>
                    <div class="result-stat-value">{drift_text}</div>
                </div>
                <div class="result-stat">
                    <div class="result-stat-label">Retraining</div>
                    <div class="result-stat-value">{retrain_text}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Raw response"):
        st.json(result)


st.set_page_config(page_title="Phisherman", layout="wide")
inject_styles()

api_url = st.sidebar.text_input("FastAPI URL", API_URL).rstrip("/")
st.sidebar.caption("Use `.venv/bin/uvicorn app:app --reload` for local runs.")

render_hero(api_url)

url_tab, manual_tab = st.tabs(["URL scan", "Manual signals"])

with url_tab:
    render_section("Check by URL", "Enter the link once. Phisherman extracts the public signals and asks the reputation API.")
    with st.container(border=True):
        url = st.text_input("Website URL", placeholder="https://example.com/login")
        render_url_preview(url)
        scan_col, _ = st.columns([1, 2])
        with scan_col:
            url_clicked = st.button("Scan URL", key="scan_url_button")

with manual_tab:
    render_section("Manual check", "Override only what you know. Everything else stays on trained defaults.")
    with st.form("manual_scan_form"):
        payload = collect_fields(USER_FIELDS, columns=3)
        left, right = st.columns([1, 2])
        with left:
            manual_clicked = st.form_submit_button("Predict from manual values")
        with right:
            st.markdown(
                f'<div class="manual-note">{len(payload)} custom value(s) selected. Internal fields use backend defaults.</div>',
                unsafe_allow_html=True,
            )
    with st.expander("Fields kept on backend defaults"):
        internal_markup = "".join(
            f'<div class="field-chip"><strong>{escape(FEATURE_HELP[field][0])}</strong>'
            f'<span>{escape(FEATURE_HELP[field][1])}</span></div>'
            for field in INTERNAL_FIELDS
        )
        st.markdown(f'<div class="internal-grid">{internal_markup}</div>', unsafe_allow_html=True)

if url_clicked:
    if not url.strip():
        st.error("Enter a URL first.")
    else:
        try:
            response = requests.post(f"{api_url}/predict/url", json={"url": url}, timeout=30)
            response.raise_for_status()
            result = response.json()
        except requests.RequestException as exc:
            st.error(f"URL check failed: {exc}")
        else:
            result_card(result)

if manual_clicked:
    try:
        response = requests.post(f"{api_url}/predict", json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as exc:
        st.error(f"Prediction request failed: {exc}")
    else:
        result_card(result)
