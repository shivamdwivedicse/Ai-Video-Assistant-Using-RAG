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

    st.write("1️⃣ Extract Audio")
    st.write("2️⃣ Whisper Transcription")
    st.write("3️⃣ AI Understanding")
    st.write("4️⃣ Knowledge Extraction")
    st.write("5️⃣ RAG Knowledge Base")
    st.write("6️⃣ Ask Questions")

    st.divider()

    st.subheader("✨ Features")

    st.write("🎯 Smart Summary")
    st.write("✅ Action Items")
    st.write("🔑 Key Decisions")
    st.write("❓ Open Questions")
    st.write("📜 Full Transcript")
    st.write("💬 Video Chat")

    st.divider()

    st.caption("Python • Whisper • LangChain • Chroma • RAG")


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

st.divider()

st.subheader("🚀 Analyze a Video")

st.write(
    "Choose a YouTube URL or upload a video/audio file."
)

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

    st.header("🎯 Video Intelligence")

    st.caption(
        "Your video's AI-generated knowledge at a glance."
    )


    # ========================================================
    # TITLE
    # ========================================================

    st.subheader(
        f"🎬 {result['title']}"
    )


    # ========================================================
    # METRICS
    # ========================================================

    words = len(
        result["transcript"].split()
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "📝 Words",
            f"{words:,}",
        )

    with col2:

        st.metric(
            "🧠 Analysis",
            "AI",
        )

    with col3:

        st.metric(
            "📚 Knowledge",
            "RAG",
        )

    with col4:

        st.metric(
            "💬 Questions",
            "∞",
        )


    # ========================================================
    # SUMMARY
    # ========================================================

    st.divider()

    st.header("📋 Executive Summary")

    st.info(
        "🧠 AI-generated summary"
    )

    st.write(
        result["summary"]
    )


    # ========================================================
    # KEY INSIGHTS
    # ========================================================

    st.header("💡 Key Insights")


    col1, col2 = st.columns(2)


    with col1:

        with st.container(border=True):

            st.subheader("✅ Action Items")

            st.write(
                result["action_items"]
            )


    with col2:

        with st.container(border=True):

            st.subheader("🔑 Key Decisions")

            st.write(
                result["key_decisions"]
            )


    col1, col2 = st.columns(2)


    with col1:

        with st.container(border=True):

            st.subheader("❓ Open Questions")

            st.write(
                result["open_questions"]
            )


    with col2:

        with st.container(border=True):

            st.subheader("⚡ AI Knowledge Base")

            st.write(
                "Your transcript has been indexed "
                "and is ready for question answering."
            )


    # ========================================================
    # TRANSCRIPT
    # ========================================================

    st.divider()

    st.header("📜 Full Transcript")

    with st.expander(
        "Open full transcript"
    ):

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

    st.header("💬 Chat With Your Video")

    st.caption(
        "Ask questions about the video and get "
        "answers from the RAG system."
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

    st.divider()

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


    st.divider()

    st.subheader(
        "🎬 Ready when you are"
    )

    st.write(
        "Provide a YouTube video URL or upload a "
        "video/audio file. VidRAG AI will transform "
        "it into summaries, insights, searchable "
        "knowledge and an interactive AI chat."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🎬 VidRAG AI • Video Intelligence powered by "
    "Whisper + LLM + Chroma RAG"
)