import streamlit as st
import google.generativeai as genai
import os
import pandas as pd
from datetime import datetime

# ==========================================
# PHẦN 1: THÔNG TIN CÁ NHÂN (CẦN THAY THẾ)
# ==========================================
# [VỊ TRÍ 1]: Thay bằng API Key lấy từ Google AI Studio
GOOGLE_API_KEY = "AIzaSyBQVlrHqS7hallRI0q_Mwy8IgqE7w0pT1o"

# [VỊ TRÍ 2]: Cấu hình tính cách của Chatbot (System Instruction)
SYSTEM_PROMPT = """
Bạn là Trợ lý học tập môn Toán của Thầy [THẦY HƯNG].
Nhiệm vụ của bạn là hỗ trợ học sinh học tập theo bộ sách [KẾT NỐI TRI THỨC].

QUY TẮC SƯ PHẠM:
1. KHÔNG BAO GIỜ cho đáp án trực tiếp.
2. Nếu học sinh hỏi đáp án, hãy nói: "Thầy muốn em tự tư duy một chút, hãy thử gợi ý này nhé..."
3. Luôn sử dụng định dạng LaTeX cho công thức toán (ví dụ: $x^2 + y^2 = r^2$).
4. Nếu có nạp file PDF, hãy ưu tiên trích dẫn kiến thức từ file đó.
"""

# ==========================================
# PHẦN 2: CẤU HÌNH HỆ THỐNG
# ==========================================
st.set_page_config(page_title="Gia sư Toán AI", page_icon="📐", layout="centered")
genai.configure(api_key=GOOGLE_API_KEY)

# Tạo thư mục data nếu chưa có để bạn bỏ file PDF vào
if not os.path.exists("data"):
    os.makedirs("data")

# Giao diện Sidebar
st.sidebar.title("💎 Quản lý học tập")
hoc_sinh = st.sidebar.text_input("Nhập tên học sinh:", value="Học sinh ẩn danh")
st.sidebar.divider()

# --- Hàm nạp tài liệu PDF ---
@st.cache_resource
def load_data_files():
    data_files = []
    folder = "data"
    for filename in os.listdir(folder):
        if filename.endswith(".pdf"):
            path = os.path.join(folder, filename)
            # Tải file lên Gemini (Miễn phí)
            file_gen = genai.upload_file(path=path)
            data_files.append(file_gen)
    return data_files

knowledge_base = load_data_files()

if knowledge_base:
    st.sidebar.success(f"✅ Đã nạp {len(knowledge_base)} tài liệu SGK/Đề thi.")
else:
    st.sidebar.warning("⚠️ Chưa có file PDF nào trong thư mục 'data'.")

# --- Khởi tạo mô hình AI ---
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

# --- Quản lý lịch sử Chat ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lịch sử chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Xử lý câu hỏi của học sinh ---
if prompt := st.chat_input("Em muốn hỏi bài tập nào?"):
    # Hiển thị câu hỏi của HS
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gửi câu hỏi đến AI
    with st.chat_message("assistant"):
        # Kết hợp tài liệu và câu hỏi
        input_data = knowledge_base + [prompt]
        response = model.generate_content(input_data)
        full_response = response.text
        st.markdown(full_response)
        
    # Lưu vào lịch sử
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # [VỊ TRÍ 3]: NHẬT KÝ GIẢNG DẠY (Ghi lại để thầy theo dõi)
    # Tạm thời lưu vào file CSV để miễn phí và đơn giản. 
    # Khi dùng Streamlit Cloud, bạn có thể tải file này về xem.
    log_data = {
        "Thời gian": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "Học sinh": [hoc_sinh],
        "Câu hỏi": [prompt],
        "AI trả lời": [full_response[:100] + "..."] # Lưu ngắn gọn
    }
    df = pd.DataFrame(log_data)
    df.to_csv("nhat_ky_hoc_tap.csv", mode='a', index=False, header=not os.path.exists("nhat_ky_hoc_tap.csv"))
