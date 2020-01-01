from os.path import abspath

from flask_assets import Bundle, Environment
from webassets.filter import ExternalTool, Filter
from webassets.filter.requirejs import RequireJSFilter

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
    dep('axios', "0.19.0", "axios.js"),
]


def get_name(url: str) -> str:
    return url.split('/')[-1].split('.')[0]


class Namer(Filter):
    def input(self, in_, out, **kwargs):
        template = """
        (function(){
            let captureDeps, captureCb;

            (function(){
                function define(valueDeps, valueCb) {
                    captureDeps = valueDeps;
                    captureCb = valueCb;
                }
                define.amd = {};
                \n %s \n
            })()

            define('%s', captureDeps, captureCb);
        })();
        """

        name = get_name(kwargs['source_path'])
        out.write(template % (in_.read(), name))


e.register(
    'deps',
    Bundle(
        *urls,
        extra={'names': list(map(get_name, urls))},
        filters=[Namer()],
        output='gen/deps.js'
    ),
)

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
    from flask import Flask

    f = Flask(__name__)

    with f.app_context():
        e['deps'].build(force=True)
