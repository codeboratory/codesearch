from dataclasses import dataclass


@dataclass
class Model:
    name: str
    model_kwargs: dict


@dataclass
class Database:
    type: str
    configuration: dict


@dataclass
class Files:
    include: list[str]
    exclude: list[str]


@dataclass
class Config:
    model: Model
    database: Database
    files: Files


default = Config(
    Model(
        "nomic-ai/CodeRankEmbed",
        {
            "load_in_8bit": True
        }
    ),
    Database(
        "chromadb",
        {
            "hnsw": {
                "space": "cosine",
                "max_neighbors": 160,
                "ef_search": 1000,
                "ef_construction": 1000
            }
        }
    ),
    Files(
        [
            "ts",
            "tsx"
        ],
        [
            "test.ts",
            "spec.ts",
            "unit.ts"
        ]
    )
)
