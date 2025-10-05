def define_init(subparsers):
    index_parser = subparsers.add_parser(
        "init",
        help="Init a repo"
    )

    index_parser.add_argument(
        "path",
        help="Path to repo (e.g., ~/dev/spectoda-monorepo/)"
    )


def handle_init(args):
    print("INIT")
