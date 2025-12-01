# 🏗️ 건설공사 클레임 어드바이저 (VO/Claim Advisor)

건설 관련 문서를 분석하여 클레임 리스크를 도출하고, 3가지 페르소나(원도급사, 발주처, 중재자) 관점에서 전략을 제시하는 AI 챗봇 서비스입니다.

## 📋 주요 기능

- **📄 문서 분석**: PDF, DOCX, XLSX 등 다양한 형식의 건설 문서 업로드 및 분석
- **🎯 리스크 도출**: AI가 자동으로 클레임 리스크 Top 5 추출
- **👥 다각도 전략**: 원도급사, 발주처, 중재자 3가지 관점에서 상세 전략 제시
- **💬 대화형 AI**: 선택한 리스크에 대해 질문하고 근거 기반 답변 제공
- **⚙️ 커스터마이징**: 각 페르소나의 프롬프트를 수정하여 답변 스타일 조정 가능

## 🛠️ 기술 스택

- **Frontend**: Streamlit 1.34.0+
- **LLM**: OpenAI GPT-4o (via LangChain)
- **Vector DB**: ChromaDB (로컬 저장)
- **Search Tool**: Exa
- **Document Processing**: PyPDF, python-docx, openpyxl

## 📦 설치 방법

### 1. 필수 요구사항

- Python 3.11 이상
- OpenAI API 키 (필수)
- Exa API 키 (선택)

### 2. 라이브러리 설치

```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고, API 키를 입력합니다:

```bash
cp .env.example .env
```

`.env` 파일 내용:
```
OPENAI_API_KEY=sk-your-openai-api-key-here
EXA_API_KEY=your-exa-api-key-here  # 선택사항
```

## 🚀 실행 방법

```bash
streamlit run main.py
```

브라우저에서 자동으로 `http://localhost:8501`로 접속됩니다.

## 📖 사용 가이드

### 1단계: 문서 업로드

좌측 사이드바에서 다음 카테고리별로 문서를 업로드합니다:
- 📁 계약서
- 📁 공문서
- 📁 회의록
- 📁 이메일
- 📁 작업일보
- 📁 기타

지원 형식: PDF, DOCX, DOC, XLSX, XLS, TXT

### 2단계: 분석 시작

"🔍 분석 시작" 버튼을 클릭하여 문서를 분석합니다.
- AI가 문서를 읽고 임베딩하여 ChromaDB에 저장합니다.
- 클레임 리스크 Top 5를 자동으로 도출합니다.

### 3단계: 리스크 선택 및 질문

- 메인 화면에 표시된 5개의 리스크 중 하나를 선택합니다.
- 하단 채팅창에서 선택한 리스크에 대해 질문합니다.
- AI가 3가지 페르소나 관점에서 답변을 제공합니다.

### 4단계: 프롬프트 커스터마이징 (선택)

우측 상단의 ⚙️ 버튼을 클릭하여 설정 창을 엽니다:
- **시스템 프롬프트**: 전체 AI의 기본 동작 정의
- **Persona 1 (원도급사)**: 원도급사 관점 답변 스타일
- **Persona 2 (발주처)**: 발주처 관점 답변 스타일
- **Persona 3 (중재자)**: 중재자 관점 답변 스타일

수정 후 "💾 저장" 버튼을 클릭하면 즉시 적용됩니다.

## 📂 프로젝트 구조

```
251201/
├── main.py              # Streamlit 메인 애플리케이션
├── rag_engine.py        # RAG 엔진 (ChromaDB + LangChain)
├── utils.py             # 파일 처리 유틸리티
├── prompts.py           # 프롬프트 상수 정의
├── requirements.txt     # 의존성 패키지 목록
├── .env.example         # 환경변수 예제
├── .env                 # 환경변수 (직접 생성)
├── README.md            # 프로젝트 문서
└── chroma_db/           # ChromaDB 저장소 (자동 생성)
```

## ⚠️ 주의사항

1. **API 키**: OpenAI API 키는 필수입니다. `.env` 파일에 반드시 설정해주세요.
2. **비용**: GPT-4o 모델을 사용하므로 API 사용 비용이 발생합니다.
3. **데이터 보안**: 민감한 계약서를 업로드할 경우, 로컬 환경에서만 실행하는 것을 권장합니다.
4. **DB 초기화**: "분석 시작" 버튼을 클릭할 때마다 ChromaDB가 초기화되고 재생성됩니다.

## 🔧 트러블슈팅

### "ModuleNotFoundError" 오류 발생 시
```bash
pip install -r requirements.txt --upgrade
```

### Streamlit 버전 오류 시
```bash
pip install streamlit>=1.34.0 --upgrade
```

### ChromaDB 관련 오류 시
`chroma_db` 폴더를 삭제하고 다시 실행해보세요:
```bash
rm -rf chroma_db
streamlit run main.py
```

## 📝 업데이트 계획

- [ ] Exa 검색 통합 (외부 판례/법령 검색)
- [ ] 심화 분석 기능 구현
- [ ] 대화 히스토리 저장/불러오기
- [ ] PDF 보고서 자동 생성
- [ ] 다국어 지원 (영어)

## 📧 문의

프로젝트 관련 문의사항이 있으시면 이슈를 등록해주세요.

---

**VO/Claim Advisor** - Powered by OpenAI GPT-4o & LangChain

