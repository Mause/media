import sys
from os.path import abspath
from shlex import shlex

from flask_assets import Bundle, Environment
from webassets.filter import ExternalTool

e = Environment()

production = '--prod' in sys.argv[1:]


class Browserify(ExternalTool):
    def input(self, data, out, **kwargs):
        argv = [
            abspath('node_modules/.bin/browserify'),
            *'-p [ tsify --module es5 ]'.split(),
            kwargs['source_path'],
        ]

        if production:
            argv.extend(
                [
                    *'-g [ envify --NODE_ENV production ] '.split(),
                    *'-g uglifyify'.split(),
                ]
            )

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
