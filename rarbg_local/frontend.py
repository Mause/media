from os.path import abspath

from flask_assets import Bundle, Environment
from webassets.filter import ExternalTool

e = Environment()


class TypeScript(ExternalTool):
    def input(self, _in, out, **kw):
        argv = [
            abspath('node_modules/.bin/tsc.cmd'),
            '--outFile',
            '{output}',
            '--jsx',
            'react',
            '--module',
            'amd',
            '--esModuleInterop',
            'true',
            "--moduleResolution",
            "node",
            '--lib',
            'es2017,dom',
            kw['source_path'],
        ]
        cwd = abspath('.')
        return self.subprocess(argv, out, cwd=cwd)


dep = "https://cdnjs.cloudflare.com/ajax/libs/{}/{}/{}".format
urls = [
    dep("lodash.js", "4.17.15", "lodash.js"),
    dep("react-dom", "16.11.0", "umd/react-dom.production.min.js"),
    dep("react", "16.12.0", "umd/react.production.min.js"),
    dep("qs", "6.9.1", "qs.min.js"),
]
for url in urls:
    name = url.split('/')[-1].split('.')[0]
    e.register(name, Bundle(url, extra={'name': name}))
e.register(
    'streaming',
    Bundle(
        'streaming.tsx',
        filters=[TypeScript()],
        extra={'name': 'streaming'},
        output='gen/streaming.js',
    ),
)


if __name__ == '__main__':
    # from .main import create_app

    from flask import Flask

    f = Flask(__name__)

    with f.app_context():
        e['streaming'].build(force=True)
