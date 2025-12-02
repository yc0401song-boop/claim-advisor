import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredExcelLoader

def extract_text_from_file(uploaded_file, filename):
    """
    업로드된 파일 객체에서 텍스트를 추출합니다.
    """
    # 임시 파일로 저장
    temp_dir = "./temp_files"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    file_path = os.path.join(temp_dir, filename)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    text = ""
    try:
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            text = "\n".join([p.page_content for p in pages])
            
        elif ext in [".docx", ".doc"]:
            loader = Docx2txtLoader(file_path)
            docs = loader.load()
            text = "\n".join([d.page_content for d in docs])
            
        elif ext in [".xlsx", ".xls"]:
            loader = UnstructuredExcelLoader(file_path)
            docs = loader.load()
            text = "\n".join([d.page_content for d in docs])
            
        elif ext == ".txt":
            # txt 파일은 그냥 읽기
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
                
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        text = "Error reading file."
        
    return text

def format_documents_for_prompt(documents):
    """
    프롬프트에 넣기 좋게 문서 내용을 하나의 문자열로 합칩니다.
    documents: [(category, filename, text), ...]
    """
    formatted_text = ""
    for category, filename, text in documents:
        formatted_text += f"\n[문서: {filename} ({category})]\n"
        formatted_text += text[:2000] # 너무 길면 자름
        formatted_text += "\n" + "-"*50 + "\n"
    return formatted_text