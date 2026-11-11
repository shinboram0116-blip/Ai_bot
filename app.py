import streamlit as st
from google import genai
import pypdf
import uuid

st.set_page_config(page_title="나만의 Gemini AI 보조", page_icon="🤖", layout="wide")
st.title("🤖 나만의 Gemini AI 보조")

# Secrets 또는 사이드바 입력에서 API 키 가져오기
api_key = st.secrets.get("GEMINI_API_KEY", "")

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
    if not api_key:
        api_key = st.text_input("Google Gemini API Key", type="password")
    else:
        st.success("🔒 API 키 자동 연결됨")
    
    uploaded_file = st.file_uploader("PDF 문서 업로드 (RAG)", type=["pdf"])

current_chat = st.session_state.chats[st.session_state.current_chat_id]
messages = current_chat["messages"]

# 3. 화면 대화 출력
for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 질문 처리
if prompt := st.chat_input("질문을 입력하세요..."):
    if not api_key:
        st.error("Google Gemini API Key가 설정되지 않았습니다!")
    else:
        if len(messages) == 0:
            current_chat["title"] = prompt[:15] + ("..." if len(prompt) > 15 else "")

        messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        pdf_text = ""
        if uploaded_file is not None:
            try:
                pdf_reader = pypdf.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        pdf_text += extracted + "\n"
            except Exception as e:
                st.error(f"PDF 파일 읽기 오류: {e}")

        # 5. 히스토리 구성
        contents = []
        if pdf_text:
            contents.append({"role": "user", "parts": [{"text": f"참고 PDF 문서:\n{pdf_text}"}]})

        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        # 6. API 호출 (스트리밍 초고속 모드)
        with st.chat_message("assistant"):
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content_stream(
                    model="gemini-3.5-flash-lite",
                    contents=contents,
                )
                
                def stream_parser():
                    for chunk in response:
                        if chunk.text:
                            yield chunk.text

                full_response = st.write_stream(stream_parser())
                messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
