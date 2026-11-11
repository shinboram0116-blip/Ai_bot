import streamlit as st
from google import genai
import pypdf

# 페이지 기본 설정
st.set_page_config(page_title="나만의 Gemini AI 보조", page_icon="🤖", layout="wide")

st.title("🤖 나만의 Gemini AI 보조")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정 및 파일")
    api_key = st.text_input("Google Gemini API Key", type="password")
    
    st.markdown("---")
    uploaded_file = st.file_uploader("PDF 문서를 업로드하세요 (RAG)", type=["pdf"])

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 기존 대화 내용 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 질문 입력받기
if prompt := st.chat_input("질문을 입력하세요..."):
    if not api_key:
        st.error("왼쪽 사이드바에 Google Gemini API Key를 입력해 주세요!")
    else:
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # PDF 텍스트 추출
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

        # 프롬프트 구성 (PDF 내용이 있으면 포함)
        full_prompt = prompt
        if pdf_text:
            full_prompt = f"다음은 참고할 PDF 문서 내용입니다:\n\n{pdf_text}\n\n위 내용을 참고하여 질문에 답해주세요:\n{prompt}"

        # Gemini API 호출
        with st.chat_message("assistant"):
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=full_prompt,
                )
                answer = response.text
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
