import git

from pathlib import Path
from shared import collection, CWD
from parser import parse_file
from embed import batch_embed_passage


def get_files(repo, extensions):
    files = repo.git.ls_files(
        '--cached',
        '--others',
        '--exclude-standard',
        *[f'*.{extension}' for extension in extensions]
    ).splitlines()

    return [file for file in files if file]


def handle_index():
    repo = git.Repo(CWD, search_parent_directories=True)
    root = Path(repo.working_dir)
    files = get_files(repo, ["ts", "tsx"])

    done = 0
    for file in files:
        nodes = parse_file(str(root / file))
        document_tensors = batch_embed_passage((
            f"{file}\n\n```ts\n{node.text}\n```" for node in nodes
        ))

        if document_tensors is None:
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
