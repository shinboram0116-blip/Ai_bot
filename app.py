import os
import streamlit as st
from google import genai
from google.genai import types
import pypdf

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="내 Gemini AI 챗봇",
    page_icon="🤖",
    layout="wide"
)

# 2. 사이드바: API Key 입력 및 PDF 업로드
with st.sidebar:
    st.title("⚙️ 설정 및 파일")
    api_key = st.text_input("Google Gemini API Key", type="password")
    uploaded_file = st.file_uploader("PDF 문서를 업로드하세요 (RAG)", type=["pdf"])
    st.markdown("---")
    st.caption("2018 LG Gram Optimized App")

st.title("🤖 나만의 Gemini AI 보조")

# PDF 텍스트 추출 함수
def extract_text_from_pdf(pdf_file):
    reader = pypdf.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

# 세션 상태 초기화 (대화 기록 저장)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 기존 대화 기록 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 사용자 입력 처리
if prompt := st.chat_input("질문을 입력하세요..."):
    if not api_key:
        st.error("사이드바에 Google Gemini API Key를 먼저 입력해 주세요!")
    else:
        # 사용자 메시지 표시 및 기록
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Gemini API 클라이언트 생성
        client = genai.Client(api_key=api_key)

        # PDF 문서가 올라와 있는 경우 프롬프트에 문서 내용 포함
        final_prompt = prompt
        if uploaded_file is not None:
            with st.spinner("PDF 문서 분석 중..."):
                pdf_text = extract_text_from_pdf(uploaded_file)
                final_prompt = f"다음은 참고할 문서 내용입니다:\n\n{pdf_text}\n\n위 문서를 바탕으로 다음 질문에 답하세요: {prompt}"

        # AI 답변 생성
        with st.chat_message("assistant"):
            with st.spinner("생각 중..."):
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=final_prompt
                    )
                    st.write(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")
