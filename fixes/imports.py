import libcst as cst
from libcst.codemod import VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor
from libcst.metadata import PositionProvider


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
