import streamlit as st
import google.generativeai as genai
import os
import time
from PIL import Image

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Gia sư Toán AI",
    page_icon="🤖",
    layout="centered"
)

# =====================================================
# CSS
# =====================================================

st.markdown("""
<style>

.block-container{
    padding-top:2rem;
    padding-bottom:2rem;
}

h1{
    text-align:center;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# API KEY
# =====================================================

try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

except Exception:

    st.error("❌ Chưa cấu hình GOOGLE_API_KEY")
    st.stop()

# =====================================================
# GEMINI CONFIG
# =====================================================

genai.configure(api_key=GOOGLE_API_KEY)

# =====================================================
# SYSTEM PROMPT
# =====================================================

SYSTEM_PROMPT = """
Bạn là Gia sư Toán AI.

Nhiệm vụ:
- Giải toán THPT chi tiết
- Giải từng bước
- Giải thích dễ hiểu
- Nếu học sinh sai thì chỉ ra lỗi
"""

# =====================================================
# MODEL
# =====================================================

try:

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=SYSTEM_PROMPT
    )

except Exception as e:

    st.error(f"Lỗi model:\n{e}")
    st.stop()

# =====================================================
# SESSION STATE
# =====================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat" not in st.session_state:

    st.session_state.chat = model.start_chat(
        history=[]
    )

# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.title("⚙️ Tuỳ chọn")

    mode = st.selectbox(
        "Chế độ trả lời",
        [
            "Giải chi tiết",
            "Gợi ý",
            "Chỉ đáp số"
        ]
    )

    if st.button("🗑️ Xóa hội thoại"):

        st.session_state.messages = []

        st.session_state.chat = model.start_chat(
            history=[]
        )

        st.success("Đã xóa hội thoại")

# =====================================================
# TITLE
# =====================================================

st.title("🤖 Gia sư Toán AI")

st.markdown("""
- 📸 Gửi ảnh bài toán
- ✍️ Nhập đề trực tiếp
- 🧠 Hỏi nhiều câu liên tục
""")

# =====================================================
# UPLOAD IMAGE
# =====================================================

uploaded_pic = st.file_uploader(
    "📸 Gửi ảnh bài toán",
    type=["jpg", "jpeg", "png"]
)

img = None

if uploaded_pic:

    try:

        img = Image.open(uploaded_pic)

        img = img.resize((800, 800))

        st.image(
            img,
            caption="Ảnh đề bài",
            use_container_width=True
        )

    except Exception as e:

        st.error(f"Lỗi ảnh:\n{e}")

# =====================================================
# SHOW HISTORY
# =====================================================

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        st.markdown(msg["content"])

# =====================================================
# INPUT
# =====================================================

prompt = st.chat_input(
    "✍️ Nhập câu hỏi..."
)

# =====================================================
# PROCESS
# =====================================================

if prompt:

    final_prompt = f"""
Chế độ: {mode}

Câu hỏi:
{prompt}
"""

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):

        st.markdown(prompt)

    with st.chat_message("assistant"):

        with st.spinner("📚 Đang giải bài..."):

            try:

                content = [final_prompt]

                if img:
                    content.append(img)

                time.sleep(2)

                response = (
                    st.session_state.chat
                    .send_message(
                        content,
                        generation_config={
                            "temperature": 0.3,
                            "max_output_tokens": 1024
                        }
                    )
                )

                answer = response.text

                st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            except Exception as e:

                st.error(f"""
❌ Đã xảy ra lỗi:

{e}

💡 Có thể:
- Hết quota Gemini
- Gửi quá nhiều request
- Ảnh quá lớn
""")
