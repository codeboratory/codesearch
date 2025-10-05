import argparse
import click

from commands.init import handle_init
from commands.index import handle_index
from commands.search import handle_search
from commands.server import handle_server


@click.group(invoke_without_command=True)
def root():
    pass


@root.command()
def init():
    handle_init()


@root.command()
def index():
    handle_index()


@root.command()
@click.argument('query')
def search(query):
    handle_search(query)


@root.command()
def server():
    handle_server()


if __name__ == "__main__":
    root()
