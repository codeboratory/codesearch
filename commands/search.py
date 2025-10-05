def define_search(subparsers):
    search_parser = subparsers.add_parser(
        "search",
        help="Search indexed content"
    )

    search_parser.add_argument(
        "query",
        nargs="+",
        help="Search query"
    )


def handle_search(args):
    query = " ".join(args.query)
    print("SEARCH", query)
