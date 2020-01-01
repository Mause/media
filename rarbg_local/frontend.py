from os.path import abspath

from flask_assets import Bundle, Environment
from webassets.filter import ExternalTool

e = Environment()


class TypeScript(ExternalTool):
    def input(self, _in, out, **kw):
        argv = [
            abspath('node_modules/.bin/tsc'),
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
    dep("react-dom", "16.11.0", "umd/react-dom.development.js"),
    dep("react", "16.12.0", "umd/react.development.js"),
    dep("qs", "6.9.1", "qs.min.js"),
    dep("react-router", "5.1.2", "react-router.js"),
    dep("react-router-dom", "5.1.2", "react-router-dom.js"),
]


def get_name(url: str) -> str:
    return url.split('/')[-1].split('.')[0]


for url in urls:
    name = get_name(url)
    e.register(name, Bundle(url, extra={'names': [name]}))
e.register(
    'streaming',
    Bundle(
        'streaming.tsx',
        filters=[TypeScript()],
        extra={'names': ['streaming']},
        output='gen/streaming.js',
    ),
)


if __name__ == '__main__':
    # from .main import create_app

    from flask import Flask

    f = Flask(__name__)

    with f.app_context():
        e['streaming'].build(force=True)
