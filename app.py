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
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}
h1 {
    text-align: center;
    color: #0E1117;
}
.stChatMessage {
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# API KEY CONFIGURATION
# =====================================================

# Ưu tiên lấy từ secrets, nếu không có thì lấy từ biến môi trường
api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
elif os.getenv("GOOGLE_API_KEY"):
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.warning("⚠️ Chưa tìm thấy GOOGLE_API_KEY trong secrets hoặc biến môi trường.")
    api_key = st.text_input("Vui lòng nhập Gemini API Key của bạn:", type="password")
    if not api_key:
        st.info("💡 Bạn có thể lấy API Key tại [Google AI Studio](https://aistudio.google.com/app/apikey)")
        st.stop()

# =====================================================
# GEMINI CONFIG
# =====================================================

genai.configure(api_key=api_key)

# =====================================================
# SYSTEM PROMPT
# =====================================================

SYSTEM_PROMPT = """
Bạn là một Gia sư Toán AI chuyên nghiệp, tận tâm và vui vẻ.
Nhiệm vụ của bạn:
1. Giải các bài toán THPT (Toán 10, 11, 12) một cách chi tiết.
2. Trình bày lời giải từng bước một (step-by-step) rõ ràng.
3. Sử dụng ngôn ngữ dễ hiểu, phù hợp với học sinh.
4. Nếu đề bài mờ hoặc thiếu thông tin, hãy yêu cầu học sinh cung cấp thêm.
5. Luôn khuyến khích học sinh tự suy nghĩ và chỉ ra các lỗi sai thường gặp.
6. Sử dụng LaTeX để viết công thức toán học cho chuyên nghiệp.
"""

# =====================================================
# MODEL INITIALIZATION
# =====================================================

@st.cache_resource
def load_model():
    try:
        # Thử dùng gemini-2.0-flash, nếu lỗi thì fallback về gemini-1.5-flash
        try:
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                system_instruction=SYSTEM_PROMPT
            )
            # Test thử model
            model.generate_content("test")
            return model
        except Exception:
            return genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=SYSTEM_PROMPT
            )
    except Exception as e:
        st.error(f"Lỗi khởi tạo model: {e}")
        return None

model = load_model()
if not model:
    st.stop()

# =====================================================
# SESSION STATE
# =====================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:
    st.title("⚙️ Cấu hình")
    
    mode = st.selectbox(
        "Chế độ phản hồi",
        ["Giải chi tiết", "Gợi ý hướng làm", "Chỉ đưa ra đáp số"]
    )
    
    st.divider()
    
    if st.button("🗑️ Xóa lịch sử trò chuyện", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat = model.start_chat(history=[])
        st.rerun()

# =====================================================
# MAIN UI
# =====================================================

st.title("🤖 Gia sư Toán AI")
st.markdown("Chào mừng bạn! Hãy gửi đề bài bằng hình ảnh hoặc nhập văn bản bên dưới.")

# UPLOAD IMAGE
uploaded_pic = st.file_uploader("📸 Tải lên ảnh bài toán (JPG, PNG)", type=["jpg", "jpeg", "png"])

img = None
if uploaded_pic:
    try:
        img = Image.open(uploaded_pic)
        st.image(img, caption="Ảnh bài toán đã tải lên", use_container_width=True)
    except Exception as e:
        st.error(f"Lỗi khi đọc file ảnh: {e}")

# DISPLAY CHAT HISTORY
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# CHAT INPUT
if prompt := st.chat_input("Nhập câu hỏi của bạn ở đây..."):
    # Hiển thị tin nhắn người dùng
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Xử lý phản hồi từ AI
    with st.chat_message("assistant"):
        with st.spinner("🧠 Đang suy nghĩ..."):
            try:
                # Chuẩn bị nội dung gửi đi
                full_prompt = f"Chế độ: {mode}\n\nCâu hỏi: {prompt}"
                content_to_send = [full_prompt]
                if img:
                    content_to_send.append(img)
                
                # Gửi tin nhắn
                response = st.session_state.chat.send_message(
                    content_to_send,
                    generation_config={
                        "temperature": 0.4,
                        "max_output_tokens": 2048
                    }
                )
                
                answer = response.text
                st.markdown(answer)
                
                # Lưu vào lịch sử
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as e:
                st.error(f"❌ Có lỗi xảy ra: {e}")
                st.info("Gợi ý: Kiểm tra lại kết nối internet hoặc API Key.")
