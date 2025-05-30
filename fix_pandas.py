import os

import libcst as cst
from libcst import FlattenSentinel
from libcst.codemod import CodemodTest, VisitorBasedCodemodCommand
from libcst.matchers import (
    Arg,
    Assign,
    Attribute,
    Call,
    Name,
    OneOf,
    SaveMatchedNode,
    SimpleString,
    extract,
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

            if parent := self.get_metadata(ParentNodeProvider, query_call, None):
                select = stack[0].with_deep_changes(parent, value=select)

            new_call = cst.Call(
                func=cst.Attribute(cst.Name('session'), cst.Name('execute')),
                args=[
                    cst.Arg(select),
                ],
            )
            return new_call
        return node


class ColumnVisitor(VisitorBasedCodemodCommand):
    METADATA_DEPENDENCIES = (ParentNodeProvider,)

    def leave_Assign(
        self, original_node: cst.Assign, updated_node: cst.Assign
    ) -> cst.CSTNode:
        if not matches(
            original_node,
            Assign(
                value=Call(
                    func=Name('Column'),
                )
            ),
        ):
            return updated_node

        updated_node = updated_node.with_changes(
            value=cst.Call(
                func=cst.Name('mapped_column'),
                args=original_node.value.args,
            )
        )
        return cst.AnnAssign(
            target=updated_node.targets[0].target,
            value=updated_node.value,
            annotation=cst.Annotation(annotation=map_annotation(original_node.value)),
        )


def map_annotation(annotation: cst.CSTNode) -> cst.CSTNode:
    arg = Arg(
        value=OneOf(
            SaveMatchedNode(matcher=Name(), name='name'),
            Call(func=SaveMatchedNode(matcher=Name(), name='name')),
        )
    )

    single_matcher = Call(args=[arg])
    with_name = Call(
        args=[
            Arg(
                value=SimpleString(),
            ),
            arg,
        ]
    )
    matcher = OneOf(single_matcher, with_name)
    if res := extract(
        annotation,
        matcher,
    ):
        annotation = res['name'].value
    else:
        return annotation

    match annotation:
        case 'String':
            return cst.Name('str')
        case 'Integer':
            return cst.Name('int')
        case 'Boolean':
            return cst.Name('bool')
        case 'DateTime':
            return cst.Name('datetime')
        case _:
            raise ValueError(f'Unknown annotation: {annotation}')


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


class TestColumnVisitor(CodemodTest):
    TRANSFORM = ColumnVisitor

    def test_replace(self):
        before = '''
        class T:
            name = Column(String)
            last_name = Column(String())
            active = Column('is_active', Boolean())
        '''
        after = '''
        class T:
            name: str = mapped_column(String)
            last_name: str = mapped_column(String())
            active: bool = mapped_column('is_active', Boolean())
        '''

        self.assertCodemod(before, after)


if __name__ == '__main__':
    import libcst.tool

    libcst.tool.main(
        '',
        [
            'codemod',
            '-x',
            'fix_pandas.FixPandasVisitor',
            'rarbg_local',
        ],
    )
