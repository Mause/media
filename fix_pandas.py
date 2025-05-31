import libcst as cst
from libcst import FlattenSentinel
from libcst.codemod import VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor
from libcst.display import dump
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
from libcst.metadata import ParentNodeProvider, PositionProvider


class AddImports(VisitorBasedCodemodCommand):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def leave_Module(self, old_node: cst.CSTNode, node: cst.CSTNode) -> cst.CSTNode:
        return (
            super().leave_Module(old_node, node).visit(AddImportsVisitor(self.context))
        )

    def ani(self, mod: str, *names: str):
        for name in names:
            AddImportsVisitor.add_needed_import(self.context, mod, name)

    def get_position(self, node: cst.CSTNode) -> str:
        pos = self.get_metadata(PositionProvider, node)
        return f'{self.context.filename}:{pos.start.line}:{pos.start.column}'


class FixPandasVisitor(AddImports, VisitorBasedCodemodCommand):
    METADATA_DEPENDENCIES = (ParentNodeProvider,)

    def is_transformable(self, node: cst.Call) -> cst.Call | None:
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

        while isinstance(node, cst.Call) and isinstance(node.func, cst.Attribute):
            last = node
            node = node.func.value

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
            return last

        return None

    def get_parent_call(self, node: cst.CSTNode):
        while node:
            node = self.get_metadata(
                ParentNodeProvider,
                node,
                None,
            )
            if isinstance(node, cst.Call):
                return node
        return None

    def leave_Call(
        self, old_node: cst.Call, node: cst.Call
    ) -> cst.CSTNode | FlattenSentinel:
        if not (query_call := self.is_transformable(old_node)):
            return node

        select = cst.Call(
            func=cst.Name('select'),
            args=query_call.args,
        )

        # we need to replace the innermost call of the chain
        parent = self.get_parent_call(query_call)
        if parent is None:
            self.warn(f'Unable to rewrite: {self.get_position(old_node)}')
            return node
        if old_node.func.value is not query_call:
            select = old_node.func.value.with_deep_changes(parent.func, value=select)

        execute = cst.Call(
            func=cst.Attribute(cst.Name('session'), cst.Name('execute')),
            args=[
                cst.Arg(select),
            ],
        )
        new_call = node.with_deep_changes(node.func, value=execute)

        self.ani("sqlalchemy.future", "select")

        return new_call


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
                        slice=cst.Index(value=self.map_annotation(original_node.value))
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

    def map_annotation(self, annotation: cst.CSTNode) -> cst.CSTNode:
        if res := extract(
            annotation,
            matcher,
        ):
            name = res['name'].value
            kwargs = {
                arg.keyword.value: arg.value.value
                for arg in res['kwargs']
                if matches(arg, Arg(value=Name()))
            }
        else:
            self.warn(
                f'Unable to handle annotation: {self.get_position(annotation)}'
                f' {dump(annotation)}',
            )
            return annotation

        res = map_name(name)

        if kwargs.get('nullable') == 'True':
            self.ani('typing', 'Optional')
            res = cst.Subscript(
                value=cst.Name('Optional'),
                slice=[cst.SubscriptElement(slice=cst.Index(value=res))],
            )

        return res


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


if __name__ == '__main__':
    import libcst.tool

    libcst.tool.main(
        '',
        [
            'codemod',
            '-x',
            'fix_pandas.ColumnVisitor',
            'rarbg_local',
        ],
    )

    libcst.tool.main(
        '',
        [
            'codemod',
            '-x',
            'fix_pandas.FixPandasVisitor',
            'rarbg_local',
        ],
    )
