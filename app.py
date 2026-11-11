import streamlit as st
from google import genai
from google.genai.errors import APIError
import pypdf
import uuid

# 타이틀 및 테마 설정
st.set_page_config(page_title="AI_Bot01", page_icon="💩", layout="wide")

# 📱 아이폰 PWA 홈 화면 앱 아이콘 + 웹 파비콘 종합 연동 (캐시 방지 ?v=2 적용)
st.markdown(
    '''
    <link rel="apple-touch-icon" sizes="180x180" href="https://raw.githubusercontent.com/shinboram0116-blip/Ai_bot/main/images.jpg?v=2">
    <link rel="icon" type="image/jpeg" href="https://raw.githubusercontent.com/shinboram0116-blip/Ai_bot/main/images.jpg?v=2">
    <meta property="og:image" content="https://raw.githubusercontent.com/shinboram0116-blip/Ai_bot/main/images.jpg?v=2">
    ''',
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
                    extracted = page.extract_text()
                    if extracted:
                        pdf_text += extracted + "\n"
            except Exception as e:
                st.error(f"PDF 파일 읽기 오류: {e}")

        contents = []
        if pdf_text:
            contents.append({"role": "user", "parts": [{"text": f"참고 PDF 문서:\n{pdf_text}"}]})

        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        # 5. Gemini 3.5 Flash + 실시간 구글 검색 연동
        with st.chat_message("assistant"):
            success = False
            last_error = ""
            active_key = None
            
            for key in api_keys:
                try:
                    client = genai.Client(api_key=key)
                    response = client.models.generate_content_stream(
                        model="gemini-3.5-flash",
                        contents=contents,
                        config={"tools": [{"google_search": {}}]}
                    )
                    
                    def stream_parser():
                        for chunk in response:
                            if chunk.text:
                                yield chunk.text

                    full_response = st.write_stream(stream_parser())
                    messages.append({"role": "assistant", "content": full_response})
                    success = True
                    active_key = key
                    break
                    
                except APIError as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        last_error = str(e)
                        continue
                    else:
                        st.error(f"오류가 발생했습니다: {e}")
                        break
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")
                    break

            if not success:
                st.error(f"오류가 발생했습니다: {last_error}")
            else:
                if is_first_message:
                    try:
                        title_client = genai.Client(api_key=active_key)
                        summary_prompt = f"다음 질문을 바탕으로 대화목록에 표시할 짧은 제목(5단어 이내, 이모지 포함)을 하나만 만들어줘. 부연설명 없이 제목만 출력해.\n질문: {prompt}"
                        title_response = title_client.models.generate_content(
                            model="gemini-3.5-flash",
                            contents=summary_prompt
                        )
                        if title_response and title_response.text:
                            current_chat["title"] = title_response.text.strip()
                        else:
                            current_chat["title"] = prompt[:10] + "..."
                    except Exception:
                        current_chat["title"] = prompt[:10] + "..."
                    st.rerun()
