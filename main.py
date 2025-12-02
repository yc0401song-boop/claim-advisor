# --------------------------------------------------------------------------------
# [Streamlit Cloud 배포용 필수 설정 - 이 부분이 없으면 서버에서 에러가 납니다!]
# --------------------------------------------------------------------------------
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
# --------------------------------------------------------------------------------

"""
건설공사 클레임 어드바이저 - 메인 애플리케이션
"""
import os
import streamlit as st
from dotenv import load_dotenv
from typing import List, Tuple
import re

# 로컬 모듈 임포트
from utils import extract_text_from_file, format_documents_for_prompt
from rag_engine import RAGEngine
from prompts import (
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_PERSONA_1_PROMPT,
    DEFAULT_PERSONA_2_PROMPT,
    DEFAULT_PERSONA_3_PROMPT
)

# 환경변수 로드
load_dotenv()

# Streamlit 페이지 설정
st.set_page_config(
    page_title="VO/Claim Advisor",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 다크 테마 CSS
st.markdown("""
<style>
    /* 메인 컨테이너 스타일링 */
    .main {
        background-color: #0E1117;
    }
    
    /* 리스크 카드 스타일 */
    .risk-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #4CAF50;
        margin: 10px 0;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .risk-card:hover {
        background-color: #2E2E2E;
        border-left-color: #66BB6A;
    }
    
    .risk-card.selected {
        background-color: #2A4A2A;
        border-left-color: #81C784;
    }
    
    /* 채팅 메시지 스타일 */
    .chat-message {
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .user-message {
        background-color: #1E3A5F;
        text-align: right;
    }
    
    .assistant-message {
        background-color: #1E1E1E;
        text-align: right; /* 답변도 우측 정렬되는 문제 방지 */
    }
    
    /* 버튼 스타일 */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 50px;
        font-weight: bold;
    }
    
    /* 설정 버튼 */
    .settings-btn {
        position: absolute;
        top: 10px;
        right: 10px;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)


# 세션 상태 초기화
def initialize_session_state():
    """세션 상태 초기화"""
    if 'initialized' not in st.session_state:
        # API 키
        # Streamlit Cloud에서는 st.secrets를 우선적으로 확인합니다.
        if "OPENAI_API_KEY" in st.secrets:
             st.session_state.openai_api_key = st.secrets["OPENAI_API_KEY"]
        else:
             st.session_state.openai_api_key = os.getenv('OPENAI_API_KEY', '')
             
        st.session_state.exa_api_key = os.getenv('EXA_API_KEY', '')
        
        # 프롬프트 설정 (기본값)
        st.session_state.system_prompt = DEFAULT_SYSTEM_PROMPT
        st.session_state.persona_1_prompt = DEFAULT_PERSONA_1_PROMPT
        st.session_state.persona_2_prompt = DEFAULT_PERSONA_2_PROMPT
        st.session_state.persona_3_prompt = DEFAULT_PERSONA_3_PROMPT
        
        # 업로드된 파일들
        st.session_state.uploaded_documents = []
        
        # Risk 분석 결과
        st.session_state.risks = []
        st.session_state.risks_analyzed = False
        
        # 선택된 Risk
        st.session_state.selected_risk = None
        st.session_state.selected_risk_index = None
        
        # 채팅 히스토리
        st.session_state.chat_history = []
        
        # RAG 엔진
        st.session_state.rag_engine = None
        
        st.session_state.initialized = True


# Settings 다이얼로그
@st.dialog("⚙️ 설정 (Settings)", width="large")
def settings_dialog():
    """설정 다이얼로그 (st.dialog 사용)"""
    st.write("### 프롬프트 설정")
    st.write("각 프롬프트를 수정하여 AI의 답변 스타일을 커스터마이징할 수 있습니다.")
    
    # 시스템 프롬프트
    st.write("#### 🤖 시스템 프롬프트")
    system_prompt = st.text_area(
        "전체 챗봇의 기본 동작을 정의합니다",
        value=st.session_state.system_prompt,
        height=100,
        key="settings_system_prompt"
    )
    
    st.divider()
    
    # Persona 1
    st.write("#### 👷 Persona 1 (원도급사)")
    persona_1_prompt = st.text_area(
        "원도급사 관점의 답변 스타일",
        value=st.session_state.persona_1_prompt,
        height=100,
        key="settings_persona_1"
    )
    
    st.divider()
    
    # Persona 2
    st.write("#### 🏢 Persona 2 (발주처)")
    persona_2_prompt = st.text_area(
        "발주처 관점의 답변 스타일",
        value=st.session_state.persona_2_prompt,
        height=100,
        key="settings_persona_2"
    )
    
    st.divider()
    
    # Persona 3
    st.write("#### ⚖️ Persona 3 (중재자)")
    persona_3_prompt = st.text_area(
        "중재자 관점의 답변 스타일",
        value=st.session_state.persona_3_prompt,
        height=100,
        key="settings_persona_3"
    )
    
    st.divider()
    
    # 버튼들
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("💾 저장 (Save)", use_container_width=True, type="primary"):
            # 세션 상태 업데이트
            st.session_state.system_prompt = system_prompt
            st.session_state.persona_1_prompt = persona_1_prompt
            st.session_state.persona_2_prompt = persona_2_prompt
            st.session_state.persona_3_prompt = persona_3_prompt
            st.success("✅ 설정이 저장되었습니다!")
            st.rerun()
    
    with col2:
        if st.button("❌ 나가기 (Cancel)", use_container_width=True):
            st.rerun()


def parse_risks(risk_text: str) -> List[dict]:
    """
    Risk 분석 텍스트를 파싱하여 리스크 리스트로 변환
    """
    risks = []
    
    # 번호로 구분하여 분할
    pattern = r'\d+\.\s*\*\*([^*]+)\*\*'
    matches = re.finditer(pattern, risk_text)
    
    for match in matches:
        title = match.group(1).strip()
        start_pos = match.end()
        
        # 다음 리스크 또는 텍스트 끝까지 내용 추출
        next_match = re.search(r'\d+\.\s*\*\*', risk_text[start_pos:])
        if next_match:
            end_pos = start_pos + next_match.start()
        else:
            end_pos = len(risk_text)
        
        description = risk_text[start_pos:end_pos].strip()
        
        risks.append({
            'title': title,
            'description': description
        })
    
    return risks


def render_sidebar():
    """사이드바 렌더링"""
    with st.sidebar:
        st.title("🏗️ VO/Claim Advisor")
        st.divider()
        
        st.subheader("📂 계약 자료 Upload")
        
        categories = {
            "계약서": "contract",
            "공문서": "official",
            "회의록": "meeting",
            "이메일": "email",
            "작업일보": "daily",
            "기타": "etc"
        }
        
        uploaded_files = {}
        
        for category_name, category_key in categories.items():
            files = st.file_uploader(
                f"📁 {category_name}",
                type=['pdf', 'docx', 'doc', 'xlsx', 'xls', 'txt'],
                accept_multiple_files=True,
                key=f"upload_{category_key}"
            )
            if files:
                uploaded_files[category_name] = files
        
        st.divider()
        
        # 분석 시작 버튼
        if st.button("🔍 분석 시작", use_container_width=True, type="primary"):
            if not uploaded_files:
                st.error("⚠️ 최소 1개 이상의 파일을 업로드해주세요!")
            elif not st.session_state.openai_api_key:
                st.error("⚠️ OpenAI API 키가 없습니다! Settings -> Secrets에 키가 있는지 확인해주세요.")
            else:
                analyze_documents(uploaded_files)
        
        # 심화 분석 버튼 (비활성화)
        if st.button("📊 심화 분석", use_container_width=True, disabled=True):
            st.toast("🚧 준비 중입니다", icon="⚠️")
        
        st.divider()
        
        # 업로드된 파일 정보 표시
        if st.session_state.uploaded_documents:
            st.write("### 📋 업로드된 파일")
            for category, filename, _ in st.session_state.uploaded_documents:
                st.write(f"- **{category}**: {filename}")


def analyze_documents(uploaded_files: dict):
    """문서 분석 실행"""
    with st.spinner("📄 문서를 분석 중입니다..."):
        try:
            # RAG 엔진 초기화
            if st.session_state.rag_engine is None:
                st.session_state.rag_engine = RAGEngine(st.session_state.openai_api_key)
            
            # 데이터베이스 초기화
            st.session_state.rag_engine.reset_database()
            
            # 문서 처리
            documents = []
            for category, files in uploaded_files.items():
                for file in files:
                    text = extract_text_from_file(file, file.name)
                    documents.append((category, file.name, text))
            
            st.session_state.uploaded_documents = documents
            
            # ChromaDB에 문서 추가
            st.session_state.rag_engine.add_documents(documents)
            
            # Risk 분석 생성
            documents_text = format_documents_for_prompt(documents)
            risk_analysis = st.session_state.rag_engine.generate_risk_analysis(documents_text)
            
            # Risk 파싱
            risks = parse_risks(risk_analysis)
            
            if len(risks) >= 5:
                st.session_state.risks = risks[:5]
            else:
                # 파싱 실패 시 (API 오류 등) 전체 텍스트를 임시로 저장
                st.session_state.risks = [
                    {"title": f"Risk {i+1}", "description": "분석 결과를 불러오지 못했습니다. API Key나 파일 내용을 확인해주세요."}
                    for i in range(5)
                ]
                # 여기서 에러 내용을 화면에 보여줌
                if not risks and risk_analysis:
                     st.warning(f"AI 응답 원문: {risk_analysis[:200]}...")
            
            st.session_state.risks_analyzed = True
            st.session_state.selected_risk = None
            st.session_state.chat_history = []
            
            st.success("✅ 분석이 완료되었습니다!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")


def render_main_area():
    """메인 영역 렌더링"""
    # 설정 버튼 (우측 상단)
    col1, col2 = st.columns([9, 1])
    with col2:
        if st.button("⚙️", help="설정"):
            settings_dialog()
    
    if not st.session_state.risks_analyzed:
        # Risk 분석 전: 앱 소개
        st.title("🏗️ 건설공사 클레임 어드바이저")
        st.write("### VO/Claim Advisor에 오신 것을 환영합니다!")
        
        st.markdown("""
        #### 📌 주요 기능
        
        1. **문서 분석**: 계약서, 공문서, 회의록 등 건설 관련 문서를 업로드하면 AI가 자동으로 분석합니다.
        
        2. **클레임 리스크 도출**: 잠재적인 클레임 리스크 상위 5개를 자동으로 식별합니다.
        
        3. **다각도 전략 제시**: 원도급사, 발주처, 중재자 3가지 페르소나 관점에서 전략을 제시합니다.
        
        4. **AI 챗봇**: 선택한 리스크에 대해 질문하고 상세한 답변을 받을 수 있습니다.
        
        #### 🚀 시작하기
        
        1. 좌측 사이드바에서 문서를 카테고리별로 업로드하세요.
        2. "🔍 분석 시작" 버튼을 클릭하세요.
        3. AI가 도출한 리스크 중 하나를 선택하여 상세 분석을 받아보세요.
        
        #### ⚙️ 설정
        
        우측 상단의 ⚙️ 버튼을 클릭하여 AI 답변 스타일을 커스터마이징할 수 있습니다.
        """)
        
    else:
        # Risk 분석 후: Risk Top 5 표시
        st.title("📊 클레임 리스크 분석 결과")
        st.write("### 🎯 Risk Top 5")
        
        # 리스크 카드 표시
        for i, risk in enumerate(st.session_state.risks):
            selected_class = "selected" if st.session_state.selected_risk_index == i else ""
            
            if st.button(
                f"**{i+1}. {risk['title']}**",
                key=f"risk_btn_{i}",
                use_container_width=True,
                type="primary" if st.session_state.selected_risk_index == i else "secondary"
            ):
                st.session_state.selected_risk = risk
                st.session_state.selected_risk_index = i
                if not st.session_state.chat_history:
                    # 첫 선택 시 초기 메시지 추가
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': f"**{risk['title']}**에 대해 질문해주세요. 원도급사, 발주처, 중재자 관점에서 상세히 분석해드리겠습니다."
                    })
                st.rerun()
            
            # 리스크 설명 표시 (접기/펼치기)
            with st.expander("📝 상세 설명", expanded=False):
                st.write(risk['description'])
        
        st.divider()
        
        # 채팅 인터페이스
        if st.session_state.selected_risk:
            render_chat_interface()


def render_chat_interface():
    """채팅 인터페이스 렌더링"""
    st.write(f"### 💬 선택된 리스크: {st.session_state.selected_risk['title']}")
    
    # 채팅 히스토리 표시
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>👤 You:</strong><br>
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>🤖 AI Advisor:</strong><br>
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)
    
    st.divider()
    
    # 추가 질문 버튼 (대화가 있을 때만 표시)
    if len(st.session_state.chat_history) > 1:
        st.write("#### 💡 추천 질문")
        
        if 'follow_up_questions' not in st.session_state or not st.session_state.follow_up_questions:
            # 추가 질문 생성
            with st.spinner("질문을 생성 중..."):
                conversation_text = "\n".join([
                    f"{msg['role']}: {msg['content']}" 
                    for msg in st.session_state.chat_history[-3:]
                ])
                
                follow_ups = st.session_state.rag_engine.generate_follow_up_questions(
                    st.session_state.selected_risk['title'],
                    conversation_text
                )
                st.session_state.follow_up_questions = follow_ups
        
        # 추천 질문 버튼 표시
        cols = st.columns(3)
        for i, question in enumerate(st.session_state.follow_up_questions[:3]):
            with cols[i]:
                if st.button(f"💡 {question[:30]}...", key=f"followup_{i}", use_container_width=True):
                    process_user_question(question)
    
    # 사용자 입력
    user_input = st.chat_input("질문을 입력하세요...")
    
    if user_input:
        process_user_question(user_input)


def process_user_question(question: str):
    """사용자 질문 처리"""
    # 사용자 메시지 추가
    st.session_state.chat_history.append({
        'role': 'user',
        'content': question
    })
    
    # AI 답변 생성
    with st.spinner("🤔 분석 중..."):
        try:
            answer = st.session_state.rag_engine.generate_answer(
                question=question,
                risk_title=st.session_state.selected_risk['title'],
                system_prompt=st.session_state.system_prompt,
                persona_1_prompt=st.session_state.persona_1_prompt,
                persona_2_prompt=st.session_state.persona_2_prompt,
                persona_3_prompt=st.session_state.persona_3_prompt
            )
            
            # AI 답변 추가
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': answer
            })
            
            # 추천 질문 초기화 (새로운 질문이 생성되도록)
            st.session_state.follow_up_questions = []
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 답변 생성 중 오류가 발생했습니다: {str(e)}")


def main():
    """메인 함수"""
    initialize_session_state()
    render_sidebar()
    render_main_area()


if __name__ == "__main__":
    main()