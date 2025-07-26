from sentence_transformers import SentenceTransformer

# BGE‑M3 모델 로드 (CPU 기준)
model = SentenceTransformer("BAAI/bge-m3", device="cpu")

sentences = [
    "That is a happy person",
    "That is a happy dog",
    "That is a very happy person",
    "Today is a sunny day"
]

# 임베딩 생성 (NumPy array 반환)
embeddings = model.encode(
    sentences,
    convert_to_numpy=True,
    show_progress_bar=True,
)

print(embeddings.shape)  # e.g. (4, 1024)
