import uvloop
from rich.traceback import install

from . import main

install(show_locals=True)

if __name__ == "__main__":
    uvloop.run(main())
