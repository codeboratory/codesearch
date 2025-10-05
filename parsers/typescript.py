import tree_sitter_typescript as ts_typescript

from language import Language


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

EXPORT = f"""
(program
    (export_statement {NORMAL_DECLARATIONS}) @content
)
"""

LOCAL = f"""
(program
    {NORMAL_DECLARATIONS} @content
)
"""

BLOCK = f"""
(statement_block
    {NORMAL_DECLARATIONS} @content
)
"""

OBJECT = f"""
(object
    (pair value: {FUNCTION_DECLARATIONS}) @content
)
"""

CLASS = f"""
(class_body
    {CLASS_DECLARATIONS} @content
)
"""

language = Language(
    ts_typescript.language_typescript(),
    [EXPORT, LOCAL, BLOCK, OBJECT, CLASS],
    ["ts", "tsx"]
)
