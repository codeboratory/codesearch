import os
import git
import torch
import torch.nn.functional as F
import tree_sitter_typescript as ts_typescript
import chromadb
import argparse

from tree_sitter import Language, Parser, Query, QueryCursor
from sentence_transformers import SentenceTransformer
from transformers import AutoModel, AutoTokenizer
from chromadb.config import Settings
from pathlib import Path

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# TODO: get context (variable/function/type references) for each node
# the referenes should be minimal so for example function reference will become just a function signature and constant reference with a big object will show its keys but will omit the values

# TODO: (maybe???) group (small) variable declarations

# TODO: split code into chunks of X tokens/characters with an overlap of Y tokens/characters if necessary

# Local persistent storage
client = chromadb.PersistentClient(path="./codesearch")
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

INNER_RESULTS = 50
OUTER_RESULTS = 1

model = SentenceTransformer(
    "nomic-ai/CodeRankEmbed",
    trust_remote_code=True,
    model_kwargs={"load_in_8bit": True}
)

QUERY_PREFIX = "Represent this query for searching relevant code: "


def batch_embed(texts):
    embeddings = []

    for text in texts:
        with torch.no_grad():
            embeddings.append(model.encode(text))
        if torch.backends.mps.is_available() and model.device.type == 'mps':
            torch.mps.empty_cache()
        elif torch.cuda.is_available() and model.device.type == 'cuda':
            torch.cuda.empty_cache()

    if len(embeddings) > 0:
        return embeddings
    else:
        return None


def batch_embed_passage(texts):
    return batch_embed(texts)


def batch_embed_query(texts):
    return batch_embed([f'{QUERY_PREFIX}{text}' for text in texts])


TAG_CONTENT = "content"
TAG_COMMENT = "comment"
TAG_DECORATOR = "decorator"

NORMAL_DECLARATIONS = """
[
    (function_declaration)
    (generator_function_declaration)
    (lexical_declaration)
    (variable_declaration)
    (if_statement)
    (for_statement)
    (for_in_statement)
    (while_statement)
    (do_statement)
    (switch_statement)
    (try_statement)
]
"""

FUNCTION_DECLARATIONS = """
[
    (arrow_function)
    (function_expression)
    (generator_function)
]
"""

CLASS_DECLARATIONS = """
[
    (method_definition)
    (abstract_method_signature)
]
"""

COMMENT = f"((comment)*) @{TAG_COMMENT}"

DECORATOR = f"((decorator)*) @{TAG_DECORATOR}"

EXPORT = f"""
(program
    (export_statement {NORMAL_DECLARATIONS}) @{TAG_CONTENT}
)
"""

LOCAL = f"""
(program
    {NORMAL_DECLARATIONS} @{TAG_CONTENT}
)
"""

BLOCK = f"""
(statement_block
    {NORMAL_DECLARATIONS} @{TAG_CONTENT}
)
"""

OBJECT = f"""
(object
    (pair value: {FUNCTION_DECLARATIONS}) @{TAG_CONTENT}
)
"""

CLASS = f"""
(class_body
    {CLASS_DECLARATIONS} @{TAG_CONTENT}
)
"""

PATTERNS = [
    EXPORT,
    LOCAL,
    BLOCK,
    OBJECT,
    CLASS
]

LANGUAGES = {
    "typescript": {
        "parser": ts_typescript.language_typescript(),
        "patterns": PATTERNS
    },
}

FILETYPES = {
    # TypeScript
    "ts": LANGUAGES["typescript"],
    "tsx": LANGUAGES["typescript"],
}


class Node:
  def __init__(self, node):
    prev = node
    text = node.text.decode("utf-8")

    while(True):
        if prev.prev_sibling != None and prev.prev_sibling.type == "comment":
            prev = prev.prev_sibling
            text = prev.text.decode("utf-8") + "\n" + text
        else:
            break

    self.start = prev.start_point
    self.end = node.end_point
    self.text = text


def parse_file(filename):
    filetype = filename.split(".")[-1]
    language = FILETYPES[filetype]
    file = open(filename)
    source = file.read().encode("utf-8")
    parser = language["parser"]
    patterns = language["patterns"]
    language_instance = Language(language["parser"])
    parser_instance = Parser(language_instance)
    tree = parser_instance.parse(source)

    nodes = []

    for pattern in patterns:
        query_instance = Query(language_instance, pattern)
        query_cursor = QueryCursor(query_instance)
        captures = query_cursor.captures(tree.root_node)

        for name in captures:
            for node in captures[name]:
                nodes.append(Node(node))

    return nodes


def get_files(repo, extensions):
    files = repo.git.ls_files(
        '--cached',
        '--others',
        '--exclude-standard',
        *[f'*.{extension}' for extension in extensions]
    ).splitlines()

    return [file for file in files if file]


def index(directory, extensions):
    repo = git.Repo(directory, search_parent_directories=True)
    root = Path(repo.working_dir)
    files = get_files(repo, extensions)

    done = 0
    for file in files:
        nodes = parse_file(str(root / file))
        document_tensors = batch_embed_passage((f"{file}\n\n```ts\n{node.text}\n```" for node in nodes))

        if document_tensors == None:
            done = done + 1
            print(file, len(nodes))
            print(f"{done} / {len(files)}")
            continue

        collection.add(
            embeddings=document_tensors,
            documents=[node.text for node in nodes],
            metadatas=[{
                "file": file,
                "start": node.start[0],
                "end": node.end[0]
            } for node in nodes],
            ids=[f"{file}:{node.start[0]}:{node.end[0]}" for node in nodes]
        )

        done = done + 1
        print(file, len(nodes))
        print(f"{done} / {len(files)}")


class Answer:
    def __init__(self, file, score, start, end, document):
        self.file = file
        self.score = score
        self.start = start
        self.end = end
        self.document = document

    def sortByScore(answer):
        return answer.score


def search(query):
    query_tensors = batch_embed_query([query])
    results = collection.query(
        query_embeddings=query_tensors,
        include=["metadatas", "distances", "documents"],
        n_results=INNER_RESULTS
    )

    files = {}

    for i, metadata in enumerate(results["metadatas"][0]):
        file = metadata["file"]

        if file not in files:
            files[file] = []

        files[file].append(i)

    answers = []

    for file in files:
        for i in files[file]:
            a_score = 1 - results["distances"][0][i]
            a_metadata = results["metadatas"][0][i]
            a_start = a_metadata["start"]
            a_end = a_metadata["end"]
            a_document = results["documents"][0][i]

            answer = Answer(file, a_score, a_start, a_end, a_document)

            for j in files[file]:
                if j == i:
                    continue

                b_score = 1 - results["distances"][0][j]
                b_metadata = results["metadatas"][0][j]
                b_start = b_metadata["start"]
                b_end = b_metadata["end"]

                overlap_start = max(a_start, b_start)
                overlap_end = min(a_end, b_end)
                overlap_amount = max(0, overlap_end - overlap_start)

                b_length = b_end - b_start
                overlap = (overlap_amount / b_length) if b_length > 0 else 0

                answer.score += overlap * b_score

            answers.append(answer)

    answers.sort(
        reverse=True,
        key=Answer.sortByScore
    )

    return answers[:OUTER_RESULTS]


def main():
    parser = argparse.ArgumentParser(description="Code search and indexing tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Index subcommand
    index_parser = subparsers.add_parser("index", help="Index a directory")
    index_parser.add_argument("path", help="Path to index (e.g., ~/dev/spectoda-monorepo/)")
    index_parser.add_argument(
        "-e", "--extensions",
        nargs="+",
        default=["ts"],
        help="File extensions to index (default: ts)"
    )

    # Search subcommand
    search_parser = subparsers.add_parser("search", help="Search indexed content")
    search_parser.add_argument("query", nargs="+", help="Search query")

    args = parser.parse_args()

    if args.command == "index":
        print(f"Indexing {args.path} with extensions: {args.extensions}\n")
        index(args.path, args.extensions)

    elif args.command == "search":
        query = " ".join(args.query)
        print(f"Searching for: {query}\n")
        results = search(query)

        for result in results:
            print(result.file, result.score, "\n", result.document, "\n")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
