def define_init(subparsers):
    subparsers.add_parser(
        "init",
        help="Init a repo"
    )


def handle_init(args):
    print("INIT")
