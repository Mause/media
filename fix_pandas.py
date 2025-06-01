if __name__ == '__main__':
    import libcst.tool

    libcst.tool.main(
        '',
        [
            'codemod',
            'column.ColumnVisitor',
            'rarbg_local',
        ],
    )

    libcst.tool.main(
        '',
        [
            'codemod',
            'query.FixPandasVisitor',
            'rarbg_local',
        ],
    )
