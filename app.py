import streamlit as st
import google.generativeai as genai
import os
from PIL import Image

# 1. Cấu hình bảo mật từ Secrets
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY, transport='rest')

# 2. Thiết lập Model
SYSTEM_PROMPT = """Bạn là trợ lý dạy Toán chuyên nghiệp của thầy Hùng. 
Khi học sinh gửi ảnh đề bài hoặc câu hỏi:
1. Đọc kỹ nội dung toán học trong ảnh.
2. Hướng dẫn từng bước giải dựa trên kiến thức sách giáo khoa.
3. Tuyệt đối không cho ngay đáp án cuối cùng nếu học sinh chưa hiểu cách làm.
4. Xưng hô thân thiện, truyền cảm hứng."""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

# Hàm nạp tài liệu PDF từ thư mục data
def load_data_files():
    folder = "data"
    if not os.path.exists(folder):
        return []
    files = []
    for filename in os.listdir(folder):
        if filename.endswith(".pdf"):
            path = os.path.join(folder, filename)
            file_gen = genai.upload_file(path=path)
            files.append(file_gen)
    return files

# Giao diện Streamlit
st.set_page_config(page_title="Gia sư Toán AI - Thầy Hùng", layout="wide")
st.title("💎 Quản lý học tập & Hỗ trợ giải toán")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Nạp dữ liệu kiến thức (chỉ chạy 1 lần)
if "knowledge_base" not in st.session_state:
    with st.spinner("Đang kết nối thư viện sách giáo khoa..."):
        st.session_state.knowledge_base = load_data_files()

st.sidebar.success(f"📚 Đã sẵn sàng {len(st.session_state.knowledge_base)} tài liệu bổ trợ.")

# --- TÍNH NĂNG CHỤP ẢNH ---
st.sidebar.header("📸 Tải ảnh đề bài")
uploaded_file = st.sidebar.file_uploader("Chụp hoặc chọn ảnh bài tập", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.sidebar.image(img, caption="Ảnh đã tải lên", use_container_width=True)

# Hiển thị lịch sử chat
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Xử lý tin nhắn và hình ảnh
if prompt := st.chat_input("Em muốn hỏi gì về bài tập này?"):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thầy đang xem bài..."):
            # Nếu có ảnh, gửi kèm ảnh cho AI
            if uploaded_file:
                content = [prompt, img, *st.session_state.knowledge_base]
            else:
                content = [prompt, *st.session_state.knowledge_base]
            
            response = model.generate_content(content)
            st.markdown(response.text)
            st.session_state.chat_history.append({"role": "assistant", "content": response.text})
