import streamlit as st
import google.generativeai as genai
import os
from PIL import Image

# =========================
# CONFIG
# =========================

st.set_page_config(
    page_title="Gia sư Toán AI",
    page_icon="🤖",
    layout="centered"
)

# =========================
# API KEY
# =========================

try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("Chưa cấu hình GOOGLE_API_KEY")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# =========================
# SYSTEM PROMPT
# =========================

SYSTEM_PROMPT = """
Bạn là gia sư Toán THPT của thầy Hùng.

Nhiệm vụ:
- Giải toán chi tiết từng bước
- Giải thích dễ hiểu
- Trình bày đẹp
- Ưu tiên phương pháp nhanh
- Nếu học sinh gửi ảnh thì đọc ảnh
- Nếu học sinh sai thì chỉ ra lỗi sai

Khi trình bày:
- Dùng ký hiệu toán học
- Trình bày theo từng bước rõ ràng
"""

# =========================
# MODEL
# =========================

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

# =========================
# LOAD PDF
# =========================

@st.cache_resource
def load_knowledge():

    folder = "data"

    if not os.path.exists(folder):
        return []

    docs = []

    for file in os.listdir(folder):

        if file.endswith(".pdf"):

            path = os.path.join(folder, file)

            try:
                uploaded = genai.upload_file(path=path)
                docs.append(uploaded)

            except Exception as e:
                st.warning(f"Lỗi file {file}: {e}")

    return docs

# =========================
# SESSION STATE
# =========================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "docs" not in st.session_state:
    st.session_state.docs = load_knowledge()

if "chat" not in st.session_state:

    st.session_state.chat = model.start_chat(
        history=[]
    )

# =========================
# TITLE
# =========================

st.title("🤖 Gia sư Toán AI")

st.markdown("""
Em có thể:

- 📸 Gửi ảnh bài toán
- ✍️ Nhập đề bài
- 📘 Hỏi theo tài liệu PDF
- 🧠 Hỏi tiếp nhiều câu liên tục
""")

# =========================
# MODE
# =========================

mode = st.selectbox(
    "Chế độ trả lời",
    [
        "Giải chi tiết",
        "Gợi ý",
        "Chỉ đáp số"
    ]
)

# =========================
# UPLOAD IMAGE
# =========================

uploaded_pic = st.file_uploader(
    "📸 Gửi ảnh đề toán",
    type=["jpg", "jpeg", "png"]
)

img = None

if uploaded_pic:

    img = Image.open(uploaded_pic)

    st.image(
        img,
        caption="Ảnh đề bài",
        use_container_width=True
    )

# =========================
# SHOW OLD CHAT
# =========================

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        st.markdown(msg["content"])

# =========================
# CHAT INPUT
# =========================

prompt = st.chat_input("Nhập câu hỏi...")

if prompt:

    # thêm mode vào prompt
    final_prompt = f"""
Chế độ: {mode}

Câu hỏi học sinh:
{prompt}
"""

    # hiện user
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):

        st.markdown(prompt)

    # AI trả lời
    with st.chat_message("assistant"):

        with st.spinner("Đang giải bài..."):

            try:

                content = [final_prompt]

                # thêm ảnh
                if img:
                    content.append(img)

                # thêm PDF
                content.extend(
                    st.session_state.docs
                )

                # CHAT MEMORY
                response = (
                    st.session_state.chat
                    .send_message(content)
                )

                answer = response.text

                st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            except Exception as e:

                st.error(f"Lỗi: {e}")
