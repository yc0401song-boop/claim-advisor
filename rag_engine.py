"""
RAG 엔진: ChromaDB 및 LangChain 로직
"""
import os
from typing import List, Tuple, Dict, Any
import chromadb
# from chromadb.config import Settings (구버전 코드 삭제)
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import tiktoken

class RAGEngine:
    """RAG 엔진 클래스"""
    
    def __init__(self, openai_api_key: str):
        """
        RAG 엔진 초기화
        Args:
            openai_api_key: OpenAI API 키
        """
        self.openai_api_key = openai_api_key
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.3,
            openai_api_key=openai_api_key
        )
        
        # ChromaDB 클라이언트 초기화 (최신 버전 호환 수정)
        # 로컬 저장소 경로 설정
        db_path = os.path.join(os.getcwd(), "chroma_db")
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        
        self.collection_name = "construction_documents"
        self.collection = None
        
        # 텍스트 분할기
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=self._count_tokens,
        )
    
    def _count_tokens(self, text: str) -> int:
        """토큰 수 계산"""
        try:
            encoding = tiktoken.encoding_for_model("gpt-4")
            return len(encoding.encode(text))
        except:
            return len(text) // 4 # 예외 발생 시 대략적인 계산
    
    def reset_database(self):
        """데이터베이스 초기화 (기존 컬렉션 삭제 후 재생성)"""
        try:
            self.chroma_client.delete_collection(name=self.collection_name)
        except:
            pass
        
        # create_collection 호출 시 metadata 설정 (코사인 유사도)
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(self, documents: List[Tuple[str, str, str]]):
        """
        문서 추가 (카테고리, 파일명, 텍스트)
        Args:
            documents: [(카테고리, 파일명, 텍스트), ...] 형태의 리스트
        """
        if self.collection is None:
            self.reset_database()
        
        all_chunks = []
        all_metadatas = []
        all_ids = []
        
        doc_id = 0
        for category, filename, text in documents:
            # 텍스트를 청크로 분할
            chunks = self.text_splitter.split_text(text)
            
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) < 50:  # 너무 짧은 청크 제외
                    continue
                
                all_chunks.append(chunk)
                all_metadatas.append({
                    "category": category,
                    "filename": filename,
                    "chunk_index": i
                })
                all_ids.append(f"doc_{doc_id}_chunk_{i}")
                doc_id += 1
        
        # 임베딩 생성 및 저장
        if all_chunks:
            embeddings_list = self.embeddings.embed_documents(all_chunks)
            
            self.collection.add(
                embeddings=embeddings_list,
                documents=all_chunks,
                metadatas=all_metadatas,
                ids=all_ids
            )
    
    def retrieve_relevant_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        질의와 관련된 문서 검색
        """
        if self.collection is None:
            return []
        
        # 질의 임베딩
        query_embedding = self.embeddings.embed_query(query)
        
        # 유사도 검색
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # 결과 포맷팅
        documents = []
        # results['documents']가 존재하는지 확인
        if results and 'documents' in results and results['documents']:
            # results['documents'][0]은 첫 번째 쿼리에 대한 결과 리스트
            docs_list = results['documents'][0]
            metadatas_list = results['metadatas'][0] if 'metadatas' in results and results['metadatas'] else [{}] * len(docs_list)
            distances_list = results['distances'][0] if 'distances' in results and results['distances'] else [0] * len(docs_list)

            for i, doc_content in enumerate(docs_list):
                documents.append({
                    'content': doc_content,
                    'metadata': metadatas_list[i],
                    'distance': distances_list[i]
                })
        
        return documents
    
    def generate_risk_analysis(self, documents_text: str) -> str:
        """Risk Top 5 분석 생성"""
        from prompts import RISK_ANALYSIS_PROMPT
        
        prompt = RISK_ANALYSIS_PROMPT.format(documents=documents_text[:15000])  # 토큰 제한
        
        response = self.llm.invoke(prompt)
        return response.content
    
    def generate_answer(
        self,
        question: str,
        risk_title: str,
        system_prompt: str,
        persona_1_prompt: str,
        persona_2_prompt: str,
        persona_3_prompt: str
    ) -> str:
        """사용자 질문에 대한 답변 생성"""
        from prompts import CHATBOT_ANSWER_TEMPLATE
        
        # 관련 문서 검색
        relevant_docs = self.retrieve_relevant_documents(f"{risk_title} {question}", top_k=5)
        
        # 컨텍스트 구성
        context = ""
        for doc in relevant_docs:
            metadata = doc['metadata']
            context += f"\n[{metadata.get('category', 'Unknown')} - {metadata.get('filename', 'Unknown')}]\n"
            context += f"{doc['content']}\n"
            context += "-" * 50 + "\n"
        
        # 프롬프트 생성
        full_prompt = CHATBOT_ANSWER_TEMPLATE.format(
            risk_title=risk_title,
            question=question,
            context=context if context else "관련 문서를 찾을 수 없습니다.",
            persona_1_instruction=persona_1_prompt,
            persona_2_instruction=persona_2_prompt,
            persona_3_instruction=persona_3_prompt
        )
        
        # LLM 호출
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    def generate_follow_up_questions(self, risk_title: str, conversation_history: str) -> List[str]:
        """추가 질문 3개 생성"""
        prompt = f"""다음 클레임 리스크와 대화 내용을 바탕으로, 사용자가 추가로 궁금해할 만한 질문 3개를 제안해주세요.

**리스크**: {risk_title}

**대화 내용**:
{conversation_history[-1000:]}

각 질문은 한 줄로 작성하고, 번호를 붙여 다음 형식으로 작성해주세요:
1. [질문1]
2. [질문2]
3. [질문3]

질문은 구체적이고 실용적이어야 하며, 법적/기술적/계약적 관점을 다양하게 포함해야 합니다."""

        response = self.llm.invoke(prompt)
        
        # 응답 파싱
        questions = []
        for line in response.content.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # 번호 제거
                try:
                    question = line.split('.', 1)[-1].strip()
                except:
                    question = line
                question = question.lstrip('-').lstrip('•').strip()
                if question:
                    questions.append(question)
        
        return questions[:3]