from os.path import abspath

from flask_assets import Bundle, Environment
from webassets.filter import ExternalTool

e = Environment()


class Browserify(ExternalTool):
    def input(self, data, out, **kwargs):
        argv = [
            abspath('node_modules/.bin/browserify'),
            '-p',
            '[',
            'tsify',
            '--module',
            'es5',
            ']',
            kwargs['source_path'],
        ]
        return self.subprocess(argv, out, data, cwd=abspath('.'))


e.register(
    'streaming',
    Bundle('streaming.tsx', filters=[Browserify()], output='gen/streaming.js'),
)


if __name__ == '__main__':
    from flask import Flask

    f = Flask(__name__)

    with f.app_context():
        e.cache = False
        e.manifest = False
        e['streaming'].build(force=True)
