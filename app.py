import streamlit as st
import google.generativeai as genai
import os
import time
from PIL import Image

# =====================================================
# CẤU HÌNH TRANG
# =====================================================
st.set_page_config(
    page_title="Gia sư Toán AI - Thầy Hùng",
    page_icon="🎓",
    layout="centered"
)

# =====================================================
# GIAO DIỆN CSS TÙY CHỈNH
# =====================================================
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
    }
    .stChatMessage {
        background-color: white;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    h1 {
        color: #1E1E1E;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# QUẢN LÝ API KEY
# =====================================================
def get_api_key():
    # 1. Thử lấy từ Streamlit Secrets (Dành cho Streamlit Cloud)
    if "GOOGLE_API_KEY" in st.secrets:
        return st.secrets["GOOGLE_API_KEY"]
    # 2. Thử lấy từ biến môi trường (Dành cho Local/Docker)
    if os.getenv("GOOGLE_API_KEY"):
        return os.getenv("GOOGLE_API_KEY")
    return None

api_key = get_api_key()

if not api_key:
    st.error("🔑 **Thiếu API Key!**")
    st.info("Vui lòng thêm `GOOGLE_API_KEY` vào mục **Secrets** trên Streamlit Cloud hoặc nhập dưới đây để dùng tạm:")
    temp_key = st.text_input("Nhập Gemini API Key:", type="password")
    if temp_key:
        api_key = temp_key
    else:
        st.stop()

# Cấu hình Gemini
genai.configure(api_key=api_key)

# =====================================================
# CẤU HÌNH MODEL
# =====================================================
SYSTEM_PROMPT = """
Bạn là Gia sư Toán AI (Thầy Hùng AI).
Nhiệm vụ:
1. Giải toán THPT Việt Nam chi tiết, chính xác.
2. Trình bày các bước giải rõ ràng, có giải thích lý do tại sao làm bước đó.
3. Sử dụng ký hiệu LaTeX (ví dụ: $x^2 + y^2 = r^2$) để công thức hiển thị đẹp.
4. Nếu đề bài là ảnh, hãy đọc kỹ và trích dẫn lại đề bài trước khi giải.
5. Luôn giữ thái độ thân thiện, khích lệ học sinh.
"""

@st.cache_resource
def load_model():
    try:
        return genai.GenerativeModel(
            model_name="gemini-1.5-flash", # Dùng bản flash để nhanh và ổn định hơn trên cloud
            system_instruction=SYSTEM_PROMPT
        )
    except Exception as e:
        st.error(f"Lỗi khởi tạo Model: {e}")
        return None

model = load_model()

# =====================================================
# QUẢN LÝ TRẠNG THÁI (SESSION STATE)
# =====================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_session" not in st.session_state:
    if model:
        st.session_state.chat_session = model.start_chat(history=[])

# =====================================================
# THANH BÊN (SIDEBAR)
# =====================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3426/3426653.png", width=100)
    st.title("Gia sư Toán AI")
    st.markdown("---")
    
    mode = st.radio(
        "Chế độ học tập:",
        ["Giải chi tiết", "Gợi ý cách làm", "Kiểm tra đáp án"]
    )
    
    if st.button("🗑️ Xóa lịch sử"):
        st.session_state.messages = []
        st.session_state.chat_session = model.start_chat(history=[])
        st.rerun()
    
    st.markdown("---")
    st.caption("Phiên bản 2.0 - Tối ưu cho Streamlit Cloud")

# =====================================================
# GIAO DIỆN CHÍNH
# =====================================================
st.title("🎓 Gia sư Toán AI (Thầy Hùng)")
st.write("Gửi ảnh đề bài hoặc nhập câu hỏi toán học của bạn bên dưới.")

# Tải ảnh lên
uploaded_file = st.file_uploader("📸 Tải lên ảnh đề bài", type=["jpg", "jpeg", "png"])
input_img = None

if uploaded_file:
    input_img = Image.open(uploaded_file)
    st.image(input_img, caption="Đề bài bạn đã gửi", use_container_width=True)

# Hiển thị lịch sử chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Nhập liệu từ người dùng
if prompt := st.chat_input("Bạn muốn hỏi gì về bài toán này?"):
    
    # Lưu tin nhắn người dùng
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # AI trả lời
    with st.chat_message("assistant"):
        with st.spinner("Thầy đang suy nghĩ..."):
            try:
                full_prompt = f"Chế độ: {mode}\nCâu hỏi: {prompt}"
                
                # Chuẩn bị nội dung gửi đi (Text + Image nếu có)
                request_content = [full_prompt]
                if input_img:
                    request_content.append(input_img)
                
                response = st.session_state.chat_session.send_message(request_content)
                ai_response = response.text
                
                st.markdown(ai_response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
                st.info("Thử lại hoặc kiểm tra API Key của bạn.")
