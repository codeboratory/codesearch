from dataclasses import dataclass


@dataclass
class Model:
    name: str


@dataclass
class Database:
    type: str


@dataclass
class Config:
    model: Model
    database: Database


default = Config(
    Model("nomic-ai/CodeRankEmbed"),
    Database("chromadb")
)
