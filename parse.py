import codecs
import json
from io import BytesIO
from typing import Any

fn = './cuts_202005_archive.torrent'


class Reader:
    def __init__(self) -> None:
        self.data = open(fn, 'rb')

    def peek(self) -> bytes:
        return self.data.peek(1)[:1]

    def read_file(self) -> Any:
        res = self.read_single()
        assert self.read() == b''
        return res

    def read_single(self) -> Any:
        char = self.read()

        match char:
            case b'd':
                return self.read_dict()
            case b'l':
                return self.read_list()
            case b'i':
                return self.read_int()
            case _:
                self.data.seek(self.data.tell() - 1)
                return self.read_string()

    def read_int(self) -> int:
        res = ''
        while self.peek() != b'e':
            res += self.read().decode()
        self.end()
        return int(res)

    def end(self) -> None:
        assert self.read() == b'e'

    def read_list(self) -> list:
        res = []
        while self.peek() != b'e':
            res.append(self.read_single())
        self.end()
        return res

    def read_dict(self) -> dict:
        res: dict[str, Any] = {}
        while self.peek() != b'e':
            key = self.read_string()
            assert isinstance(key, str)
            value = self.read_single()
            res[key] = value
        self.end()
        return res

    def read_size(self) -> int:
        size = ''
        while True:
            char = self.read()
            if char == b':':
                break
            size += char.decode()
        return int(size)

    def read_string(self) -> str | bytes:
        data = self.data.read(self.read_size())
        try:
            return data.decode()
        except ValueError:
            return data

    def read(self) -> bytes:
        return self.data.read(1)


data = Reader().read_file()

pieces_data = BytesIO(data['info']['pieces'])

pieces = [
    codecs.encode(pieces_data.read(20), 'hex').decode() for _ in data['info']['files']
]

data['info']['pieces'] = pieces

with open('file.json', 'w') as fh:
    json.dump(
        data,
        fh,
        indent=2,
        default=repr,
    )

# torrent = Torrent.read('./cuts_202005_archive.torrent')
# rich.print(torrent)

# bencode_rs.bdecode(open('./cuts_202005_archive.torrent', 'rb').read())
