import libcst as cst
from libcst import FlattenSentinel
from libcst.codemod import VisitorBasedCodemodCommand
from libcst.matchers import (
    Attribute,
    Call,
    Name,
    OneOf,
    matches,
)
from libcst.metadata import ParentNodeProvider

from .imports import AddImports


class QueryVisitor(AddImports, VisitorBasedCodemodCommand):
    METADATA_DEPENDENCIES = (ParentNodeProvider,)

    def is_transformable(self, node: cst.Call) -> cst.Call | None:
        if not matches(
            node,
            Call(
                func=Attribute(
                    attr=OneOf(Name('all'), Name('first'), Name('one_or_none'))
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
        new_call = new_call.with_deep_changes(
            new_call.func,
            value=cst.Call(
                func=cst.Attribute(
                    value=new_call.func.value,
                    attr=cst.Name('scalars'),
                )
            ),
        )

        self.ani("sqlalchemy.future", "select")

        return new_call
