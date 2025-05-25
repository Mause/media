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
    def leave_Call(
        self, old_node: cst.Call, node: cst.Call
    ) -> cst.CSTNode | FlattenSentinel:
        if (
            isinstance(node.func, cst.Attribute)
            and node.func.value.value == 'session'
            and node.func.attr.value == 'query'
        ):
            # Replace pd with importorskip
            new_call = cst.Call(
                func=cst.Name('importorskip'),
                args=[cst.Arg(cst.SimpleString("'pandas'"))],
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
