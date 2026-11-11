import streamlit as st
from google import genai
from google.genai.errors import APIError
import pypdf
import uuid

# 타이틀 및 테마 설정
st.set_page_config(page_title="AI_Bot01", page_icon="💩", layout="wide")

# 📱 아이폰 PWA 홈 화면 앱 아이콘(표지) 연동 (images.jpg 적용)
st.markdown(
    '<link rel="apple-touch-icon" sizes="180x180" href="https://raw.githubusercontent.com/shinboram0116-blip/Ai_bot/main/images.jpg">',
    unsafe_allow_html=True
)

st.title("💩 AI_Bot01")

# Secrets 또는 사용자 입력에서 API 키 가져오기
raw_api_keys = st.secrets.get("GEMINI_API_KEY", "")

# 1. 세션 상태 초기화
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat_id" not in st.session_state or st.session_state.current_chat_id not in st.session_state.chats:
    new_id = str(uuid.uuid4())
    st.session_state.chats[new_id] = {"title": "새 대화", "messages": []}
    st.session_state.current_chat_id = new_id

# 2. 사이드바 구성
with st.sidebar:
    st.header("⚙️ 설정 및 대화")
    
    if st.button("➕ 새 대화 시작하기", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.chats[new_id] = {"title": "새 대화", "messages": []}
        st.session_state.current_chat_id = new_id
        st.rerun()

    st.markdown("---")
    st.subheader("💬 대화 목록")
    
    chat_ids = list(st.session_state.chats.keys())
    chat_titles = [st.session_state.chats[cid]["title"] for cid in chat_ids]
    
    current_index = chat_ids.index(st.session_state.current_chat_id)
    selected_index = st.radio(
        "대화 선택",
        range(len(chat_ids)),
        format_func=lambda i: chat_titles[i],
        index=current_index,
        label_visibility="collapsed"
    )
    
    if chat_ids[selected_index] != st.session_state.current_chat_id:
        st.session_state.current_chat_id = chat_ids[selected_index]
        st.rerun()

    if st.button("🗑️ 현재 대화 삭제하기", use_container_width=True, type="secondary"):
        del st.session_state.chats[st.session_state.current_chat_id]
        if not st.session_state.chats:
            new_id = str(uuid.uuid4())
            st.session_state.chats[new_id] = {"title": "새 대화", "messages": []}
            st.session_state.current_chat_id = new_id
        else:
            st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
        st.rerun()

    st.markdown("---")
    if not raw_api_keys:
        input_key = st.text_input("Google Gemini API Key", type="password")
        api_keys = [k.strip() for k in input_key.split(",") if k.strip()]
    else:
        api_keys = [k.strip() for k in raw_api_keys.split(",") if k.strip()]
        st.success("🔒 API 키 자동 연결됨")
    
    uploaded_file = st.file_uploader("PDF 문서 업로드 (RAG)", type=["pdf"])

current_chat = st.session_state.chats[st.session_state.current_chat_id]
messages = current_chat["messages"]

# 3. 메인 대화 창 출력
for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 질문 처리
if prompt := st.chat_input("질문을 입력하세요..."):
    if not api_keys:
        st.error("Google Gemini API Key가 설정되지 않았습니다!")
    else:
        is_first_message = (len(messages) == 0)

        messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        pdf_text = ""
        if uploaded_file is not None:
            try:
                pdf_reader = pypdf.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
