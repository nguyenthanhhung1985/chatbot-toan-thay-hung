import streamlit as st
import google.generativeai as genai
import os
from PIL import Image

# 1. Cấu hình bảo mật (Lấy từ Secrets của Streamlit)
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("Lỗi: Thầy chưa cấu hình GOOGLE_API_KEY trong phần Secrets!")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# 2. Khởi tạo Model Gemini 1.5 Flash
SYSTEM_PROMPT = "Bạn là trợ lý dạy Toán của thầy Hùng. Hãy nhìn ảnh học sinh gửi và hướng dẫn giải chi tiết."
model = genai.GenerativeModel("gemini-1.5-flash")
# Hàm nạp tài liệu PDF từ thư mục data
def load_knowledge():
    folder = "data"
    if not os.path.exists(folder): return []
    docs = []
    for f in os.listdir(folder):
        if f.endswith(".pdf"):
            path = os.path.join(folder, f)
            docs.append(genai.upload_file(path=path))
    return docs

# Giao diện
st.set_page_config(page_title="Gia sư Toán AI", layout="centered")
st.title("🤖 Gia sư Toán của thầy Hùng")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "docs" not in st.session_state:
    st.session_state.docs = load_knowledge()

# --- KHU VỰC GỬI ẢNH NGAY TRÊN CHAT ---
st.write("---")
uploaded_pic = st.file_uploader("📸 Gửi ảnh đề bài tại đây (Chụp ảnh hoặc chọn file)", type=["jpg", "jpeg", "png"])
if uploaded_pic:
    img_display = Image.open(uploaded_pic)
    st.image(img_display, caption="Ảnh em vừa gửi", width=300)
st.write("---")

# Hiển thị tin nhắn cũ
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Xử lý tin nhắn mới
if prompt := st.chat_input("Em muốn hỏi thầy điều gì?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thầy đang xem bài..."):
            # Chuẩn bị nội dung gửi cho AI (Lời nhắn + Ảnh + Tài liệu PDF)
            content_to_send = [prompt]
            if uploaded_pic:
                content_to_send.append(img_display)
            content_to_send.extend(st.session_state.docs)
            
            response = model.generate_content(content_to_send)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
