from tree_sitter import Language, Parser, Query, QueryCursor
from parsers.typescript import language as language_typescript


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


LANGUAGES = [
    language_typescript
]

FILETYPES = {
    extension: language for language in LANGUAGES for extension in language.extensions
}


def parse_file(filename):
    filetype = filename.split(".")[-1]
    language = FILETYPES[filetype]

    if language is None:
        return []

    file = open(filename)
    source = file.read().encode("utf-8")

    language_instance = Language(language.parser)
    parser_instance = Parser(language_instance)
    tree = parser_instance.parse(source)

    nodes = []

    for pattern in language.patterns:
        query_instance = Query(language_instance, pattern)
        query_cursor = QueryCursor(query_instance)
        captures = query_cursor.captures(tree.root_node)

        for name in captures:
            for node in captures[name]:
                nodes.append(Node(node))

    return nodes
