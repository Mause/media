import ast
import fileinput
import json

import rich
import tree_sitter
import tree_sitter_typescript
from pydantic import RootModel

lang = tree_sitter.Parser(
    tree_sitter.Language(tree_sitter_typescript.language_typescript())
)


def non_null[T](t: T | None) -> T:
    assert t is not None
    return t


def checked_cast[T](t: type[T], val: object) -> T:
    return RootModel[t].model_validate(val).root  # type: ignore[valid-type]


def walk(node: tree_sitter.Node) -> object:
    match node.type:
        case "call_expression":
            name = non_null(node.named_children[0].text).decode()
            args = node.named_children[1]
            return (name, walk(args))
        case "arguments":
            return [walk(subnode) for subnode in node.named_children]
        case "string":
            return ast.literal_eval(non_null(node.text).decode())
        case "object":
            return dict(
                checked_cast(tuple, walk(subnode)) for subnode in node.named_children
            )
        case "pair":
            key = walk(node.named_children[0])
            value = walk(node.named_children[1])
            if key == 'body':
                value = json.loads(checked_cast(str, value))
            return (key, value)
        case "expression_statement":
            return walk(node.named_children[0])
        case "program":
            return walk(node.named_children[0])
        case _:
            raise Exception(node.type)


def main() -> None:
    line = b'\n'.join(fileinput.input(mode='rb'))

    parsed = lang.parse(line)

    res = walk(parsed.root_node)

    _, args = checked_cast(tuple[str, tuple[str, dict]], res)

    rich.print(args)


if __name__ == '__main__':
    main()
