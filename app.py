import streamlit as st
from dotenv import load_dotenv

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
# PREMIUM DARK UI
# ============================================================

st.markdown(
    """
    <style>

    /* Main background */
    .stApp {
        background:
            radial-gradient(circle at 15% 10%, rgba(99,102,241,.16), transparent 28%),
            radial-gradient(circle at 85% 15%, rgba(139,92,246,.13), transparent 28%),
            #070a12;
    }

    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #090c14;
        border-right: 1px solid rgba(255,255,255,.08);
    }

    /* Hero */
    .hero {
        text-align: center;
        padding: 55px 10px 35px;
    }

    .badge {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 30px;
        background: rgba(99,102,241,.12);
        border: 1px solid rgba(129,140,248,.25);
        color: #a5b4fc;
        font-weight: 700;
        font-size: 13px;
        letter-spacing: 1px;
    }

    .hero-title {
        font-size: 64px;
        line-height: 1.05;
        font-weight: 800;
        letter-spacing: -3px;
        margin-top: 20px;
        color: #f8fafc;
    }

    .gradient-text {
        color: #8b5cf6;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 18px;
        line-height: 1.6;
        margin-top: 15px;
    }

    /* Cards */
    .card {
        background: rgba(255,255,255,.035);
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 18px;
    }

    /* Metrics */
    .metric-card {
        text-align: center;
        padding: 20px 10px;
        background: rgba(255,255,255,.035);
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 18px;
    }

    .metric-icon {
        font-size: 28px;
    }

    .metric-value {
        color: #f8fafc;
        font-size: 25px;
        font-weight: 800;
        margin-top: 5px;
    }

    .metric-label {
        color: #64748b;
        font-size: 12px;
    }

    /* Result cards */
    .result-card {
        background: rgba(255,255,255,.035);
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 18px;
        padding: 20px;
        min-height: 130px;
    }

    .result-icon {
        font-size: 28px;
    }

    .result-title {
        color: #f8fafc;
        font-size: 17px;
        font-weight: 700;
        margin-top: 8px;
    }

    /* Input */
    div[data-testid="stTextInput"] input {
        background: rgba(255,255,255,.04);
        border: 1px solid rgba(255,255,255,.1);
        color: white;
        border-radius: 12px;
    }

    /* Button */
    .stButton button {
        border-radius: 12px;
        font-weight: 700;
        min-height: 44px;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #475569;
        font-size: 12px;
        padding: 40px 0 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


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

    st.title("🎬 VidRAG AI")

    st.caption("AI Video Intelligence")

    st.divider()

    st.subheader("⚙️ How it works")

    st.write("🎵 Extract Audio")
    st.write("🎙️ Whisper Transcription")
    st.write("🧠 AI Understanding")
    st.write("🔎 Knowledge Extraction")
    st.write("📚 RAG Knowledge Base")
    st.write("💬 Ask Questions")

    st.divider()

    st.subheader("✨ Features")

    st.write("🎯 Smart Summary")
    st.write("✅ Action Items")
    st.write("🔑 Key Decisions")
    st.write("❓ Open Questions")
    st.write("📜 Full Transcript")
    st.write("💬 Video Chat")

    st.divider()

    st.caption("Python • Whisper • LangChain • RAG")


# ============================================================
# HERO
# ============================================================

st.markdown("## ✦ VIDRAG AI")

st.title("Turn Videos Into Knowledge.")

st.caption(
    "Watch less. Understand more. "
    "Transform long videos into searchable AI knowledge."
)

st.success("🟢 AI SYSTEM READY")


# ============================================================
# INPUT SECTION
# ============================================================

st.subheader("🚀 Analyze a Video")

st.caption(
    "Paste a YouTube URL or enter a local video/audio file path."
)

source = st.text_input(
    "Video URL / File Path",
    placeholder="https://youtube.com/watch?v=..."
)

col1, col2 = st.columns([3, 1])

with col1:

    language = st.selectbox(
        "Language",
        ["english", "hinglish"]
    )

with col2:

    st.write("")

    analyze = st.button(
        "⚡ Analyze",
        use_container_width=True
    )


# ============================================================
# PIPELINE
# ============================================================

if analyze:

    if not source.strip():

        st.warning("Please enter a YouTube URL or local file path.")

    else:

        st.session_state.result = None
        st.session_state.chat_history = []

        progress = st.progress(0)
        status = st.empty()

        try:

            # Audio
            status.info("🎵 Processing audio...")
            progress.progress(15)

            chunks = process_input(source.strip())

            # Transcription
            status.info("🎙️ Transcribing with Whisper...")
            progress.progress(30)

            transcript = transcribe_all(
                chunks,
                language=language
            )

            # AI analysis
            status.info("🧠 Understanding the video...")
            progress.progress(50)

            title = generate_title(transcript)

            summary = summarize(transcript)

            # Extraction
            status.info("🔎 Extracting important information...")
            progress.progress(70)

            action_items = extract_action_items(transcript)

            decisions = extract_key_decisions(transcript)

            questions = extract_questions(transcript)

            # RAG
            status.info("📚 Building knowledge base...")
            progress.progress(90)

            rag_chain = build_rag_chain(transcript)

            progress.progress(100)

            status.success("✨ Analysis completed successfully!")

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

        except Exception as e:

            progress.empty()

            st.error("❌ Something went wrong.")

            with st.expander("View error details"):

                st.exception(e)


# ============================================================
# RESULTS
# ============================================================

result = st.session_state.result


if result:

    st.divider()

    st.header("🎯 Video Intelligence")

    st.caption("Your video's AI-generated knowledge at a glance.")

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    st.markdown(
        f"### 🎬 {result['title']}"
    )

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    words = len(result["transcript"].split())

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-icon">📝</div>
                <div class="metric-value">{words:,}</div>
                <div class="metric-label">Words</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:

        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-icon">🧠</div>
                <div class="metric-value">AI</div>
                <div class="metric-label">Analysis</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:

        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-icon">📚</div>
                <div class="metric-value">RAG</div>
                <div class="metric-label">Knowledge</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:

        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-icon">💬</div>
                <div class="metric-value">∞</div>
                <div class="metric-label">Questions</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    st.header("📋 Executive Summary")

    st.markdown(
        '<div class="result-card">🧠 AI generated summary</div>',
        unsafe_allow_html=True
    )

    st.write(result["summary"])

    # --------------------------------------------------------
    # INSIGHTS
    # --------------------------------------------------------

    st.header("💡 Key Insights")

    c1, c2 = st.columns(2)

    with c1:

        st.markdown(
            """
            <div class="result-card">
                <div class="result-icon">✅</div>
                <div class="result-title">Action Items</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write(result["action_items"])

    with c2:

        st.markdown(
            """
            <div class="result-card">
                <div class="result-icon">🔑</div>
                <div class="result-title">Key Decisions</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write(result["key_decisions"])

    c1, c2 = st.columns(2)

    with c1:

        st.markdown(
            """
            <div class="result-card">
                <div class="result-icon">❓</div>
                <div class="result-title">Open Questions</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write(result["open_questions"])

    with c2:

        st.markdown(
            """
            <div class="result-card">
                <div class="result-icon">⚡</div>
                <div class="result-title">AI Knowledge Base</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write(
            "Your transcript has been indexed and is ready "
            "for question answering."
        )

    # --------------------------------------------------------
    # TRANSCRIPT
    # --------------------------------------------------------

    st.header("📜 Transcript")

    with st.expander("Open full transcript"):

        st.text_area(
            "Transcript",
            result["transcript"],
            height=400,
            label_visibility="collapsed"
        )

    # --------------------------------------------------------
    # CHAT
    # --------------------------------------------------------

    st.header("💬 Chat With Your Video")

    st.caption(
        "Ask questions about the video and get answers from the RAG system."
    )

    for message in st.session_state.chat_history:

        with st.chat_message(message["role"]):

            st.write(message["content"])

    question = st.chat_input(
        "Ask anything about this video..."
    )

    if question:

        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": question
            }
        )

        with st.chat_message("user"):

            st.write(question)

        with st.chat_message("assistant"):

            with st.spinner("Thinking..."):

                try:

                    answer = ask_question(
                        result["rag_chain"],
                        question
                    )

                    st.write(answer)

                    st.session_state.chat_history.append(
                        {
                            "role": "assistant",
                            "content": answer
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

    st.divider()

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "🎙️ Transcription",
            "Whisper"
        )

    with c2:
        st.metric(
            "🧠 Intelligence",
            "LLM"
        )

    with c3:
        st.metric(
            "📚 Search",
            "RAG"
        )

    st.markdown("### 🎬 Ready when you are")

    st.write(
        "Enter a YouTube video above and VidRAG AI will "
        "turn it into summaries, insights and an interactive "
        "knowledge base."
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("## ✦ VIDRAG AI")

st.title("Turn Videos Into Knowledge.")

st.write(
    "Watch less. Understand more. "
    "Transform long videos into searchable AI knowledge."
)

st.success("🟢 AI SYSTEM READY")