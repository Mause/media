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
