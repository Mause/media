import logging

import libcst as cst
from libcst import FlattenSentinel
from libcst.codemod import CodemodTest, VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor
from libcst.matchers import (
    Arg,
    Assign,
    Attribute,
    Call,
    Name,
    OneOf,
    SaveMatchedNode,
    SimpleString,
    ZeroOrMore,
    extract,
    matches,
)
from libcst.metadata import ParentNodeProvider

import_from = cst.ImportFrom(
    cst.Name('pytest'), names=[cst.ImportAlias(cst.Name('importorskip'))]
)
logger = logging.getLogger(__name__)


class AddImports(VisitorBasedCodemodCommand):
    def leave_Module(self, old_node, node):
        return node.visit(AddImportsVisitor(self.context))

    def ani(self, mod: str, *names: str):
        for name in names:
            AddImportsVisitor.add_needed_import(self.context, mod, name)


class FixPandasVisitor(AddImports, VisitorBasedCodemodCommand):
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

            parent = next(
                (
                    item
                    for item in stack
                    if isinstance(item, cst.Call) and query_call in item.func.children
                ),
                None,
            )
            if parent is None:
                logger.warning('Unable to rewrite')
                return node
            select = stack[0].with_deep_changes(parent.func, value=select)

            execute = cst.Call(
                func=cst.Attribute(cst.Name('session'), cst.Name('execute')),
                args=[
                    cst.Arg(select),
                ],
            )
            new_call = node.with_deep_changes(node.func, value=execute)

            self.ani("sqlalchemy.future", "select")

            return new_call
        return node


class ColumnVisitor(AddImports, VisitorBasedCodemodCommand):
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
        anno = cst.Annotation(
            annotation=cst.Subscript(
                value=cst.Name('Mapped'),
                slice=[
                    cst.SubscriptElement(
                        slice=cst.Index(value=map_annotation(original_node.value))
                    )
                ],
            )
        )

        self.ani("sqlalchemy.orm", "Mapped", 'mapped_column')

        return cst.AnnAssign(
            target=updated_node.targets[0].target,
            value=updated_node.value,
            annotation=anno,
        )


def column(*args: Arg):
    return Call(
        func=Name(
            value='Column',
        ),
        args=[
            *args,
            SaveMatchedNode(
                matcher=ZeroOrMore(
                    Arg(
                        keyword=Name(),
                    ),
                ),
                name='kwargs',
            ),
        ],
    )


arg = Arg(
    value=OneOf(
        SaveMatchedNode(matcher=Name(), name='name'),
        Call(func=SaveMatchedNode(matcher=Name(), name='name')),
    )
)

matcher = OneOf(
    column(arg),
    column(
        Arg(
            value=SimpleString(),
        ),
        arg,
    ),
    column(
        arg,
        Arg(
            value=Call(
                func=Name(
                    value='ForeignKey',
                ),
            ),
        ),
    ),
)


def map_annotation(annotation: cst.CSTNode) -> cst.CSTNode:
    if res := extract(
        annotation,
        matcher,
    ):
        name = res['name'].value
        kwargs = {arg.keyword.value: arg.value.value for arg in res['kwargs']}
    else:
        return annotation

    res = map_name(name)

    if kwargs.get('nullable') == 'True':
        res = cst.Subscript(
            value=cst.Name('Optional'),
            slice=[cst.SubscriptElement(slice=cst.Index(value=res))],
        )

    return res


def map_name(name: str) -> cst.Name:
    match name:
        case 'String':
            return cst.Name('str')
        case 'Integer':
            return cst.Name('int')
        case 'Boolean':
            return cst.Name('bool')
        case 'DateTime':
            return cst.Name('datetime')
        case 'Enum':
            return cst.Name('Never')
        case _:
            raise ValueError(f'Unknown annotation: {name}')


class Testy(CodemodTest):
    TRANSFORM = FixPandasVisitor

    def test_replace(self):
        before = '''
        session.query(Model).filter(Model.id == 1).all()
        '''
        after = '''
        from sqlalchemy.future import select
        from sqlalchemy.orm import Mapped, mapped_column

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
            phone = Column(String, nullable=True)
        '''
        after = '''
        from sqlalchemy.future import select
        from sqlalchemy.orm import Mapped, mapped_column

        class T:
            name: Mapped[str] = mapped_column(String)
            last_name: Mapped[str] = mapped_column(String())
            active: Mapped[bool] = mapped_column('is_active', Boolean())
            phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
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
