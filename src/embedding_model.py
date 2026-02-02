"""
임베딩 모델 모듈
- 한국어 지원 다국어 임베딩 모델
- 상품 제목을 768차원 벡터로 변환
"""
from sentence_transformers import SentenceTransformer
import numpy as np
from functools import lru_cache

# 모델 이름 (한국어 지원 다국어 모델)
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

# 싱글톤 패턴으로 모델 로딩 (한 번만 로드)
_model = None

def get_model() -> SentenceTransformer:
    """임베딩 모델 인스턴스 반환 (싱글톤)"""
    global _model
    if _model is None:
        print(f"🔄 임베딩 모델 로딩 중: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        print(f"✅ 모델 로딩 완료! (차원: {_model.get_sentence_embedding_dimension()})")
    return _model


def encode_text(text: str) -> list:
    """
    텍스트를 임베딩 벡터로 변환
    
    Args:
        text: 변환할 텍스트 (예: 상품 제목)
    
    Returns:
        768차원 벡터 (list)
    """
    model = get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def encode_texts_batch(texts: list, batch_size: int = 32, show_progress: bool = True) -> list:
    """
    여러 텍스트를 배치로 임베딩 변환 (대량 처리용)
    
    Args:
        texts: 텍스트 리스트
        batch_size: 배치 크기
        show_progress: 진행률 표시 여부
    
    Returns:
        임베딩 벡터 리스트
    """
    model = get_model()
    embeddings = model.encode(
        texts, 
        batch_size=batch_size, 
        normalize_embeddings=True,
        show_progress_bar=show_progress
    )
    return embeddings.tolist()


def get_embedding_dimension() -> int:
    """임베딩 벡터 차원 반환"""
    return get_model().get_sentence_embedding_dimension()


# 테스트용
if __name__ == "__main__":
    # 테스트
    test_texts = [
        "패딩",
        "따뜻한 겨울 아우터",
        "다운자켓 푸퍼",
        "남성용 롱패딩"
    ]
    
    print("\n🧪 임베딩 테스트")
    print("=" * 50)
    
    embeddings = encode_texts_batch(test_texts, show_progress=False)
    
    for text, emb in zip(test_texts, embeddings):
        print(f"'{text}' → 벡터 차원: {len(emb)}")
    
    # 유사도 테스트
    from numpy import dot
    from numpy.linalg import norm
    
    def cosine_sim(a, b):
        return dot(a, b) / (norm(a) * norm(b))
    
    print("\n📊 코사인 유사도")
    print("-" * 50)
    base = embeddings[0]  # "패딩"
    for text, emb in zip(test_texts, embeddings):
        sim = cosine_sim(base, emb)
        print(f"'패딩' ↔ '{text}': {sim:.4f}")
