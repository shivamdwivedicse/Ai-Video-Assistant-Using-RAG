import os
import streamlit as st
from dotenv import load_dotenv
from yt_dlp.utils import DownloadError

from utils.audio_processor import process_input

from core.transcriber import transcribe_all

from core.summarizer import summarize, generate_title

from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)

from core.rag_engine import build_rag_chain, ask_question


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

st.set_page_config(
    page_title="VidRAG AI",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# THEME / CSS  (UI only)
# ============================================================

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

:root {
    --bg: #0A0E1A;
    --panel: #111830;
    --panel-2: #172042;
    --line: rgba(140, 160, 255, 0.16);
    --text: #E8ECFF;
    --muted: #8D97BF;
    --violet: #7C5CFF;
    --cyan: #22D3EE;
    --green: #34D399;
}

html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif;
    color: var(--text);
}

.stApp {
    background:
        radial-gradient(900px 480px at 12% -8%, rgba(124, 92, 255, 0.22), transparent 60%),
        radial-gradient(800px 420px at 95% 4%, rgba(34, 211, 238, 0.14), transparent 60%),
        var(--bg);
}

header[data-testid="stHeader"] { background: transparent; }

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1180px;
}

h1, h2, h3, h4 {
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: -0.01em;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: #0C1226;
    border-right: 1px solid var(--line);
}

.brand {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    background: linear-gradient(90deg, #fff, #B9A8FF 60%, var(--cyan));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.brand-sub { color: var(--muted); font-size: 0.85rem; margin-bottom: 0.4rem; }

.side-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 0.95rem;
    margin: 0.3rem 0 0.6rem 0;
    color: var(--text);
}

.step {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.5rem 0.65rem;
    margin-bottom: 0.35rem;
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 10px;
    font-size: 0.88rem;
}

.step .n {
    flex: 0 0 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 600;
    background: linear-gradient(135deg, var(--violet), var(--cyan));
    color: #fff;
}

.feat {
    display: inline-block;
    padding: 0.3rem 0.65rem;
    margin: 0 0.3rem 0.4rem 0;
    border-radius: 999px;
    background: var(--panel-2);
    border: 1px solid var(--line);
    font-size: 0.8rem;
}

.stack { color: var(--muted); font-size: 0.78rem; }

/* ---------- Hero ---------- */
.hero {
    position: relative;
    padding: 2.6rem 2.4rem;
    border-radius: 22px;
    border: 1px solid var(--line);
    background:
        linear-gradient(135deg, rgba(124, 92, 255, 0.16), rgba(34, 211, 238, 0.06) 55%, rgba(17, 24, 48, 0.9));
    overflow: hidden;
    margin-bottom: 1.4rem;
}

.hero::after {
    content: "";
    position: absolute;
    right: -70px; top: -70px;
    width: 260px; height: 260px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(124, 92, 255, 0.35), transparent 70%);
}

.hero .tag {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.3rem 0.8rem;
    border-radius: 999px;
    border: 1px solid rgba(52, 211, 153, 0.4);
    background: rgba(52, 211, 153, 0.1);
    color: var(--green);
    font-size: 0.8rem;
    font-weight: 500;
}

.hero .dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.6);
    animation: pulse 1.8s infinite;
}

@keyframes pulse {
    0%   { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.55); }
    70%  { box-shadow: 0 0 0 10px rgba(52, 211, 153, 0); }
    100% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }
}

.hero h1 {
    font-size: clamp(2.2rem, 5vw, 3.6rem);
    line-height: 1.05;
    font-weight: 700;
    margin: 1rem 0 0.8rem 0;
    padding: 0;
    color: #fff;
}

.hero h1 span {
    background: linear-gradient(90deg, #B9A8FF, var(--cyan));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero p {
    max-width: 640px;
    color: var(--muted);
    font-size: 1.05rem;
    margin: 0;
}

.pipeline {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 1.4rem;
}

.pipeline .chip {
    padding: 0.35rem 0.8rem;
    border-radius: 8px;
    background: rgba(10, 14, 26, 0.6);
    border: 1px solid var(--line);
    font-size: 0.82rem;
    color: var(--text);
}

/* ---------- Section headings ---------- */
.sec {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.45rem;
    font-weight: 600;
    margin: 0.2rem 0 0.2rem 0;
}

.sec-sub { color: var(--muted); font-size: 0.92rem; margin-bottom: 0.9rem; }

/* ---------- Widgets ---------- */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--panel);
    border: 1px solid var(--line) !important;
    border-radius: 16px;
}

div[data-testid="stMetric"] {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 1rem 1.1rem;
}

div[data-testid="stMetricLabel"] { color: var(--muted); }

div[data-testid="stMetricValue"] {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--violet), #5B8CFF 60%, var(--cyan));
    border: 0;
    color: #fff;
    font-weight: 600;
    border-radius: 12px;
    padding: 0.65rem 1rem;
    box-shadow: 0 8px 24px rgba(124, 92, 255, 0.35);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 12px 30px rgba(124, 92, 255, 0.5);
}

.stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
    background: var(--panel-2) !important;
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
}

section[data-testid="stFileUploadDropzone"], div[data-testid="stFileUploaderDropzone"] {
    background: var(--panel-2);
    border: 1.5px dashed rgba(124, 92, 255, 0.55);
    border-radius: 14px;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.4rem;
    border-bottom: 1px solid var(--line);
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 10px 10px 0 0;
    padding: 0.55rem 1rem;
    color: var(--muted);
}

.stTabs [aria-selected="true"] { color: #fff; }

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, var(--violet), var(--cyan));
}

div[data-testid="stChatMessage"] {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 0.9rem 1rem;
}

div[data-testid="stExpander"] {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 14px;
}

hr { border-color: var(--line) !important; }

.card-head {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 1.1rem;
    margin-bottom: 0.4rem;
}

.video-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    line-height: 1.2;
    margin: 0.2rem 0 1rem 0;
}

.empty {
    text-align: center;
    padding: 2rem 1rem;
    border: 1px dashed var(--line);
    border-radius: 18px;
    background: rgba(17, 24, 48, 0.5);
}

.empty h3 { margin-bottom: 0.3rem; }
.empty p { color: var(--muted); max-width: 560px; margin: 0 auto; }

.footer { text-align: center; color: var(--muted); font-size: 0.82rem; padding-top: 0.5rem; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def section(title, subtitle=None):
    st.markdown(f'<div class="sec">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="sec-sub">{subtitle}</div>', unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

if "result" not in st.session_state:
    st.session_state.result = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown('<div class="brand">🎬 VidRAG AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">AI Video Intelligence</div>', unsafe_allow_html=True)

    st.divider()

    st.markdown('<div class="side-title">How it works</div>', unsafe_allow_html=True)

    steps = [
        "Extract Audio",
        "Whisper Transcription",
        "AI Understanding",
        "Knowledge Extraction",
        "RAG Knowledge Base",
        "Ask Questions",
    ]

    st.markdown(
        "".join(
            f'<div class="step"><div class="n">{i}</div><div>{s}</div></div>'
            for i, s in enumerate(steps, start=1)
        ),
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown('<div class="side-title">Features</div>', unsafe_allow_html=True)

    features = [
        "🎯 Smart Summary",
        "✅ Action Items",
        "🔑 Key Decisions",
        "❓ Open Questions",
        "📜 Full Transcript",
        "💬 Video Chat",
    ]

    st.markdown(
        "".join(f'<span class="feat">{f}</span>' for f in features),
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown(
        '<div class="stack">Python • Whisper • LangChain • Chroma • RAG</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">
        <span class="tag"><span class="dot"></span>AI system ready</span>
        <h1>Turn videos into <span>knowledge.</span></h1>
        <p>Watch less. Understand more. Transform long videos into
        searchable AI knowledge you can summarize, extract from and chat with.</p>
        <div class="pipeline">
            <div class="chip">🎵 Audio</div>
            <div class="chip">🎙️ Whisper</div>
            <div class="chip">🧠 LLM</div>
            <div class="chip">📚 Chroma RAG</div>
            <div class="chip">💬 Chat</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# INPUT SECTION
# ============================================================

section("🚀 Analyze a video", "Paste a YouTube URL or upload a video/audio file.")

input_method = st.radio(
    "Choose input method",
    ["🎬 YouTube URL", "📁 Upload Video / Audio"],
    horizontal=True,
)


source = None


# ============================================================
# YOUTUBE INPUT
# ============================================================

if input_method == "🎬 YouTube URL":

    source = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
    )

    st.info(
        "💡 YouTube downloading depends on YouTube's current "
        "server-side restrictions. If downloading fails, "
        "use the Upload option below."
    )


# ============================================================
# FILE UPLOAD INPUT
# ============================================================

else:

    uploaded_file = st.file_uploader(
        "Upload Video / Audio",
        type=[
            "mp4",
            "mp3",
            "wav",
            "m4a",
            "webm",
            "mov",
            "ogg",
        ],
        help="Upload a video or audio file for AI analysis.",
    )

    if uploaded_file is not None:

        os.makedirs("downloads", exist_ok=True)

        file_path = os.path.join(
            "downloads",
            uploaded_file.name,
        )

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        source = file_path

        st.success(
            f"✅ Uploaded: {uploaded_file.name}"
        )


# ============================================================
# LANGUAGE + ANALYZE
# ============================================================

col1, col2 = st.columns([3, 1])

with col1:

    language = st.selectbox(
        "Transcription Language",
        ["english", "hinglish"],
    )

with col2:

    st.write("")

    analyze = st.button(
        "⚡ Analyze Video",
        use_container_width=True,
        type="primary",
    )


# ============================================================
# PIPELINE
# ============================================================

if analyze:

    if not source:

        st.warning(
            "⚠️ Please provide a YouTube URL "
            "or upload a video/audio file."
        )

        st.stop()


    # Clear previous result

    st.session_state.result = None
    st.session_state.chat_history = []


    progress = st.progress(0)

    status = st.empty()


    try:

        # ----------------------------------------------------
        # STEP 1 — AUDIO
        # ----------------------------------------------------

        status.info("🎵 Processing audio...")

        progress.progress(10)

        chunks = process_input(source.strip())


        # ----------------------------------------------------
        # STEP 2 — TRANSCRIPTION
        # ----------------------------------------------------

        status.info("🎙️ Transcribing with Whisper...")

        progress.progress(30)

        transcript = transcribe_all(
            chunks,
            language=language,
        )


        # ----------------------------------------------------
        # STEP 3 — AI UNDERSTANDING
        # ----------------------------------------------------

        status.info("🧠 Understanding the video...")

        progress.progress(50)

        title = generate_title(transcript)

        summary = summarize(transcript)


        # ----------------------------------------------------
        # STEP 4 — INFORMATION EXTRACTION
        # ----------------------------------------------------

        status.info(
            "🔎 Extracting important information..."
        )

        progress.progress(65)

        action_items = extract_action_items(
            transcript
        )

        decisions = extract_key_decisions(
            transcript
        )

        questions = extract_questions(
            transcript
        )


        # ----------------------------------------------------
        # STEP 5 — RAG
        # ----------------------------------------------------

        status.info(
            "📚 Building RAG knowledge base..."
        )

        progress.progress(85)

        rag_chain = build_rag_chain(
            transcript
        )


        # ----------------------------------------------------
        # COMPLETE
        # ----------------------------------------------------

        progress.progress(100)

        status.success(
            "✨ Video analysis completed successfully!"
        )


        # ----------------------------------------------------
        # SAVE RESULT
        # ----------------------------------------------------

        st.session_state.result = {

            "title": title,

            "transcript": transcript,

            "summary": summary,

            "action_items": action_items,

            "key_decisions": decisions,

            "open_questions": questions,

            "rag_chain": rag_chain,
        }


        st.rerun()


    except DownloadError as e:

        progress.empty()
        status.empty()

        st.error(
            "❌ YouTube video could not be downloaded."
        )

        st.warning(
            "YouTube is currently blocking the cloud "
            "server request (HTTP 403)."
        )

        st.info(
            "💡 Switch to '📁 Upload Video / Audio' "
            "and upload the same video. The complete "
            "Whisper + AI + RAG pipeline will still work."
        )

        with st.expander("Technical details"):

            st.code(
                str(e),
                language="text",
            )


    except Exception as e:

        progress.empty()
        status.empty()

        st.error(
            "❌ Something went wrong while processing "
            "the video."
        )

        with st.expander("View error details"):

            st.exception(e)


# ============================================================
# RESULTS
# ============================================================

result = st.session_state.result


if result:

    st.divider()

    section("🎯 Video intelligence", "Your video's AI-generated knowledge at a glance.")


    # ========================================================
    # TITLE
    # ========================================================

    st.markdown(
        f'<div class="video-title">🎬 {result["title"]}</div>',
        unsafe_allow_html=True,
    )


    # ========================================================
    # METRICS
    # ========================================================

    words = len(
        result["transcript"].split()
    )

    read_min = max(1, round(words / 200))

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "📝 Words",
            f"{words:,}",
        )

    with col2:

        st.metric(
            "⏱️ Read time",
            f"{read_min} min",
        )

    with col3:

        st.metric(
            "📚 Knowledge base",
            "Indexed",
        )

    with col4:

        st.metric(
            "💬 Video chat",
            "Live",
        )

    st.write("")


    # ========================================================
    # TABS: SUMMARY / INSIGHTS / TRANSCRIPT
    # ========================================================

    tab_summary, tab_insights, tab_transcript = st.tabs(
        ["📋 Summary", "💡 Key Insights", "📜 Transcript"]
    )


    # ---------------- SUMMARY ----------------

    with tab_summary:

        with st.container(border=True):

            st.markdown(
                '<div class="card-head">📋 Executive Summary</div>',
                unsafe_allow_html=True,
            )

            st.write(
                result["summary"]
            )


    # ---------------- INSIGHTS ----------------

    with tab_insights:

        col1, col2 = st.columns(2)

        with col1:

            with st.container(border=True):

                st.markdown(
                    '<div class="card-head">✅ Action Items</div>',
                    unsafe_allow_html=True,
                )

                st.write(
                    result["action_items"]
                )

        with col2:

            with st.container(border=True):

                st.markdown(
                    '<div class="card-head">🔑 Key Decisions</div>',
                    unsafe_allow_html=True,
                )

                st.write(
                    result["key_decisions"]
                )

        col1, col2 = st.columns(2)

        with col1:

            with st.container(border=True):

                st.markdown(
                    '<div class="card-head">❓ Open Questions</div>',
                    unsafe_allow_html=True,
                )

                st.write(
                    result["open_questions"]
                )

        with col2:

            with st.container(border=True):

                st.markdown(
                    '<div class="card-head">⚡ AI Knowledge Base</div>',
                    unsafe_allow_html=True,
                )

                st.write(
                    "Your transcript has been indexed "
                    "and is ready for question answering."
                )


    # ---------------- TRANSCRIPT ----------------

    with tab_transcript:

        st.text_area(
            "Transcript",
            result["transcript"],
            height=400,
            label_visibility="collapsed",
        )


    # ========================================================
    # CHAT
    # ========================================================

    st.divider()

    section(
        "💬 Chat with your video",
        "Ask questions about the video and get answers from the RAG system.",
    )


    # Previous messages

    for message in st.session_state.chat_history:

        with st.chat_message(
            message["role"]
        ):

            st.write(
                message["content"]
            )


    # New question

    question = st.chat_input(
        "Ask anything about this video..."
    )


    if question:

        # User message

        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": question,
            }
        )


        with st.chat_message("user"):

            st.write(question)


        # AI response

        with st.chat_message("assistant"):

            with st.spinner(
                "🧠 Thinking..."
            ):

                try:

                    answer = ask_question(
                        result["rag_chain"],
                        question,
                    )

                    st.write(answer)


                    st.session_state.chat_history.append(
                        {
                            "role": "assistant",
                            "content": answer,
                        }
                    )


                except Exception as e:

                    st.error(
                        f"Unable to answer: {e}"
                    )


# ============================================================
# EMPTY STATE
# ============================================================

else:

    st.write("")

    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "🎙️ Transcription",
            "Whisper",
        )


    with col2:

        st.metric(
            "🧠 Intelligence",
            "LLM",
        )


    with col3:

        st.metric(
            "📚 Search",
            "RAG",
        )


    st.write("")

    st.markdown(
        """
        <div class="empty">
            <h3>🎬 Ready when you are</h3>
            <p>Provide a YouTube video URL or upload a video/audio file.
            VidRAG AI will turn it into summaries, insights, searchable
            knowledge and an interactive AI chat.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    '<div class="footer">🎬 VidRAG AI • Video Intelligence powered by '
    'Whisper + LLM + Chroma RAG</div>',
    unsafe_allow_html=True,
)