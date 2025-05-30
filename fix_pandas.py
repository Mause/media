import os

import libcst as cst
from libcst import FlattenSentinel
from libcst.codemod import CodemodTest, VisitorBasedCodemodCommand
from libcst.matchers import (
    Attribute,
    Call,
    Name,
    OneOf,
    matches,
)
from libcst.metadata import ParentNodeProvider

os.environ['LIBCST_PARSER_TYPE'] = 'pure'

import_from = cst.ImportFrom(
    cst.Name('pytest'), names=[cst.ImportAlias(cst.Name('importorskip'))]
)


class FixPandasVisitor(VisitorBasedCodemodCommand):
    METADATA_DEPENDENCIES = (ParentNodeProvider,)

    def is_transformable(
        self, node: cst.Call
    ) -> tuple[cst.Call, list[cst.CSTNode]] | None:
        if not matches(
            node,
            Call(
                func=Attribute(
                    attr=OneOf(Name('all'), Name('first')),
                ),
            ),
            metadata_resolver=self,
        ):
            return None

        stack = [node.func.value]
        while isinstance(node, cst.Call) and isinstance(node.func, cst.Attribute):
            last = node
            node = node.func.value
            stack.append(node)

        if matches(
            last,
            Call(
                func=Attribute(
                    value=Name('session'),
                    attr=Name('query'),
                ),
            ),
            metadata_resolver=self,
        ):
            return last, stack

        return None

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
    import libcst.tool

    libcst.tool.main(
        '', ['codemod', '-x', 'fix_pandas.FixPandasVisitor', 'rarbg_local']
    )
