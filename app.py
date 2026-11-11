import streamlit as st
from google import genai
import pypdf

st.set_page_config(page_title="나만의 Gemini AI 보조", page_icon="🤖", layout="wide")
st.title("🤖 나만의 Gemini AI 보조")

# Streamlit Secrets 또는 사이드바 입력에서 API 키 가져오기
api_key = st.secrets.get("GEMINI_API_KEY", "")

with st.sidebar:
    st.header("⚙️ 설정 및 파일")
    # Secrets에 키가 없는 경우에만 수동 입력창 표시
    if not api_key:
        api_key = st.text_input("Google Gemini API Key", type="password")
    else:
        st.success("🔒 API 키가 자동으로 연결되었습니다!")
    
    st.markdown("---")
    uploaded_file = st.file_uploader("PDF 문서를 업로드하세요 (RAG)", type=["pdf"])

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("질문을 입력하세요..."):
    if not api_key:
        st.error("Google Gemini API Key가 설정되지 않았습니다!")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
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

        full_prompt = prompt
        if pdf_text:
            full_prompt = f"다음은 참고할 PDF 문서 내용입니다:\n\n{pdf_text}\n\n위 내용을 참고하여 질문에 답해주세요:\n{prompt}"

        with st.chat_message("assistant"):
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=full_prompt,
                )
                if response and response.text:
                    answer = response.text
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error("응답은 왔으나 텍스트가 비어 있습니다.")
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
