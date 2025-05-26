import os

import libcst as cst
from libcst import FlattenSentinel
from libcst.codemod import CodemodTest, VisitorBasedCodemodCommand

os.environ['LIBCST_PARSER_TYPE'] = 'pure'

import_from = cst.ImportFrom(
    cst.Name('pytest'), names=[cst.ImportAlias(cst.Name('importorskip'))]
)


def should_transform(node):
    alias = node.names[0]
    if not isinstance(alias, cst.ImportAlias):
        return False

    name = alias.name.value

    if not isinstance(name, cst.Name):
        return False

    return name.value == 'pandas'


class FixPandasVisitor(VisitorBasedCodemodCommand):
    def is_transformable(self, node: cst.Call) -> bool:
        if not isinstance(node.func, cst.Attribute):
            return False
        if not isinstance(node.func.attr, cst.Name):
            return False
        if node.func.attr.value not in {'all', 'first'}:
            return False

        stack = [node.func.value]
        while isinstance(node, cst.Call) and isinstance(node.func, cst.Attribute):
            last = node
            node = node.func.value
            stack.append(node)

        if (
            isinstance(last.func, cst.Attribute)
            and isinstance(last.func.value, cst.Name)
            and last.func.value.value == 'session'
            and last.func.attr.value == 'query'
        ):
            return last

    def leave_Call(
        self, old_node: cst.Call, node: cst.Call
    ) -> cst.CSTNode | FlattenSentinel:
        if query_call := self.is_transformable(node):
            new_call = cst.Call(
                func=cst.Attribute(cst.Name('session'), cst.Name('execute')),
                args=[
                    cst.Arg(
                        cst.Call(
                            func=cst.Name('select'),
                            args=query_call.args,
                        )
                    ),
                ],
            )
            return new_call
        return node


class Testy(CodemodTest):
    TRANSFORM = FixPandasVisitor

    def test_replace(self):
        before = '''
        session.query(Model).filter(Model.id == 1).all()
        '''
        after = '''
        session.execute(select(Model).where(Model.id == 1)).all()
        '''

        self.assertCodemod(before, after)


if __name__ == '__main__':
    import unittest

    unittest.main()

    import libcst.tool

    libcst.tool.main(
        '', ['codemod', '-x', 'fix_pandas.FixPandasVisitor', 'rarbg_local']
    )
