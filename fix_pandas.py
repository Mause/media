import os

import libcst as cst
from libcst import FlattenSentinel
from libcst.codemod import CodemodTest, VisitorBasedCodemodCommand
from libcst.metadata import ParentNodeProvider

os.environ['LIBCST_PARSER_TYPE'] = 'pure'

import_from = cst.ImportFrom(
    cst.Name('pytest'), names=[cst.ImportAlias(cst.Name('importorskip'))]
)


class FixPandasVisitor(VisitorBasedCodemodCommand):
    METADATA_DEPENDENCIES = (ParentNodeProvider,)

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
            return last, stack

    def leave_Call(
        self, old_node: cst.Call, node: cst.Call
    ) -> cst.CSTNode | FlattenSentinel:
        if a := self.is_transformable(node):
            (query_call, stack) = a

            select = cst.Call(
                func=cst.Name('select'),
                args=query_call.args,
            )

            self.get_metadata(ParentNodeProvider, query_call)
            stack[0].with_deep_changes(query_call, value=select)

            new_call = cst.Call(
                func=cst.Attribute(cst.Name('session'), cst.Name('execute')),
                args=[
                    cst.Arg(select),
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
