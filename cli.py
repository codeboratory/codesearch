import argparse

from commands.init import define_init, handle_init
from commands.index import define_index, handle_index
from commands.search import define_search, handle_search


def handle_command(parser):
    args = parser.parse_args()

    match args.command:
        case "init":
            handle_init(args)
        case "index":
            handle_index(args)
        case "search":
            handle_search(args)
        case _:
            parser.print_help()


def main():
    parser = argparse.ArgumentParser(
        description="Code search and indexing tool"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Command to execute"
    )

    define_init(subparsers)
    define_index(subparsers)
    define_search(subparsers)

    handle_command(parser)


if __name__ == "__main__":
    main()
