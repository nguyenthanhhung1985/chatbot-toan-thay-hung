import streamlit as st
import google.generativeai as genai
import os
import time
from PIL import Image

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Gia sư Toán AI",
    page_icon="🤖",
    layout="centered"
)

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.block-container{
    padding-top:2rem;
    padding-bottom:2rem;
}

h1{
    text-align:center;
}

.stChatMessage{
    border-radius:15px;
    padding:10px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# API KEY
# =========================================================

try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

except Exception:

    st.error("❌ Chưa cấu hình GOOGLE_API_KEY trong Secrets")
    st.stop()

# =========================================================
# GEMINI CONFIG
# =========================================================

genai.configure(api_key=GOOGLE_API_KEY)

# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
Bạn là Gia sư Toán AI của thầy Hùng.

Nhiệm vụ:
- Giải toán THPT chi tiết từng bước
- Trình bày dễ hiểu
- Không bỏ qua bước quan trọng
- Nếu học sinh làm sai thì chỉ ra lỗi sai
- Nếu học sinh gửi ảnh thì phân tích ảnh
- Ưu tiên cách giải ngắn gọn
- Trình bày rõ ràng đẹp mắt
"""

# =========================================================
# LOAD MODEL
# =========================================================

try:

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-8b",
        system_instruction=SYSTEM_PROMPT
    )

except Exception as e:

    st.error(f"❌ Lỗi khởi tạo Gemini:\n{e}")
    st.stop()

# =========================================================
# LOAD PDF KNOWLEDGE
# =========================================================

@st.cache_resource
def load_knowledge():

    folder = "data"

    docs = []

    if not os.path.exists(folder):
        return docs

    pdf_files = [
        f for f in os.listdir(folder)
        if f.endswith(".pdf")
    ]

    # Chỉ load 1 PDF để giảm quota
    pdf_files = pdf_files[:1]

    for file in pdf_files:

        try:

            path = os.path.join(folder, file)

            uploaded = genai.upload_file(path=path)

            docs.append(uploaded)

        except Exception as e:

            st.warning(f"⚠️ Lỗi PDF {file}: {e}")

    return docs

# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "docs" not in st.session_state:
    st.session_state.docs = load_knowledge()

if "chat" not in st.session_state:

    st.session_state.chat = model.start_chat(
        history=[]
    )

# =========================================================
# SIDEBAR
# =========================================================

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

    st.markdown("---")

    if st.button("🗑️ Xóa hội thoại"):

        st.session_state.messages = []

        st.session_state.chat = model.start_chat(
            history=[]
        )

        st.success("Đã xóa hội thoại")

    st.markdown("---")

    st.markdown("""
### 📚 Chức năng

✅ Giải toán THPT  
✅ Đọc ảnh bài toán  
✅ Hỗ trợ PDF  
✅ Nhớ hội thoại  
✅ Giải từng bước  
""")

# =========================================================
# TITLE
# =========================================================

st.title("🤖 Gia sư Toán AI")

st.markdown("""
Xin chào 👋

Em có thể:

- 📸 Gửi ảnh bài toán
- ✍️ Nhập đề trực tiếp
- 📘 Hỏi theo tài liệu PDF
- 🧠 Hỏi tiếp nhiều câu liên tục
""")

# =========================================================
# IMAGE UPLOAD
# =========================================================

uploaded_pic = st.file_uploader(
    "📸 Gửi ảnh bài toán",
    type=["jpg", "jpeg", "png"]
)

img = None

if uploaded_pic:

    try:

        img = Image.open(uploaded_pic)

        # Resize để giảm quota
        img = img.resize((800, 800))

        st.image(
            img,
            caption="Ảnh đề bài",
            use_container_width=True
        )

    except Exception as e:

        st.error(f"❌ Lỗi đọc ảnh:\n{e}")

# =========================================================
# SHOW CHAT HISTORY
# =========================================================

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        st.markdown(msg["content"])

# =========================================================
# CHAT INPUT
# =========================================================

prompt = st.chat_input(
    "✍️ Nhập câu hỏi của em..."
)

# =========================================================
# PROCESS CHAT
# =========================================================

if prompt:

    final_prompt = f"""
Chế độ trả lời: {mode}

Câu hỏi:
{prompt}
"""

    # -----------------------------------------------------
    # USER MESSAGE
    # -----------------------------------------------------

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):

        st.markdown(prompt)

    # -----------------------------------------------------
    # ASSISTANT RESPONSE
    # -----------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("📚 Thầy đang giải bài..."):

            try:

                content = [final_prompt]

                # Thêm ảnh nếu có
                if img:
                    content.append(img)

                # Chỉ gửi PDF nếu người dùng hỏi PDF
                if "pdf" in prompt.lower():

                    if len(st.session_state.docs) > 0:

                        content.extend(
                            st.session_state.docs
                        )

                # Delay chống spam quota
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

                # Lưu lịch sử
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            except Exception as e:

                error_text = f"""
❌ Đã xảy ra lỗi:

{e}

💡 Gợi ý:
- Chờ 30-60 giây rồi hỏi lại
- Giảm kích thước ảnh
- Không gửi quá nhiều câu liên tục
- Kiểm tra quota Gemini
"""

                st.error(error_text)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_text
                })

# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption("🚀 Gia sư Toán AI • Streamlit + Gemini")
