from libcst.codemod import CodemodTest

from fixes import ColumnVisitor, QueryVisitor


class Testy(CodemodTest):
    TRANSFORM = QueryVisitor

    def test_replace(self):
        before = '''
        session.query(Model).filter(Model.id == 1).all()
        '''
        after = '''
        from sqlalchemy.future import select

        session.execute(select(Model).filter(Model.id == 1)).scalars().all()
        '''

        self.assertCodemod(before, after)

    def test_no_chain(self):
        before = '''
        session.query(User).first()
        '''
        after = '''
        from sqlalchemy.future import select

        session.execute(select(User)).scalars().first()
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
        from sqlalchemy.orm import Mapped, mapped_column
        from typing import Optional

        class T:
            name: Mapped[str] = mapped_column(String)
            last_name: Mapped[str] = mapped_column(String())
            active: Mapped[bool] = mapped_column('is_active', Boolean())
            phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
        '''

        self.assertCodemod(before, after)


if __name__ == '__main__':
    import unittest

    unittest.main()
