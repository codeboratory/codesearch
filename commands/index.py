import git

from pathlib import Path
from shared import collection
from parser import parse_file
from embed import batch_embed_passage


def define_index(subparsers):
    index_parser = subparsers.add_parser(
        "index",
        help="Index a directory"
    )

    index_parser.add_argument(
        "path",
        help="Path to index (e.g., ~/dev/spectoda-monorepo/)"
    )

    index_parser.add_argument(
        "-e", "--extensions",
        nargs="+",
        default=["ts"],
        help="File extensions to index (default: ts)"
    )


def get_files(repo, extensions):
    files = repo.git.ls_files(
        '--cached',
        '--others',
        '--exclude-standard',
        *[f'*.{extension}' for extension in extensions]
    ).splitlines()

    return [file for file in files if file]


def handle_index(args):
    repo = git.Repo(args.path, search_parent_directories=True)
    root = Path(repo.working_dir)
    files = get_files(repo, args.extensions)

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
