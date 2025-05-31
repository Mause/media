import libcst as cst
from libcst.codemod import VisitorBasedCodemodCommand
from libcst.display import dump
from libcst.matchers import (
    Arg,
    Assign,
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

from .imports import AddImports


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
