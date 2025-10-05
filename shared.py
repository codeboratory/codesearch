import os
import chromadb

from sentence_transformers import SentenceTransformer

os.environ["TOKENIZERS_PARALLELISM"] = "false"

CWD = "~/dev/spectoda-monorepo"

client = chromadb.PersistentClient(path=f"{CWD}/.codesearch")

collection = client.get_or_create_collection(
    name="nodes",
    configuration={
        "hnsw": {
            "space": "cosine",
            "max_neighbors": 160,
            "ef_search": 1000,
            "ef_construction": 1000
        }
    }
)

model = SentenceTransformer(
    "nomic-ai/CodeRankEmbed",
    trust_remote_code=True,
    model_kwargs={"load_in_8bit": True}
)
