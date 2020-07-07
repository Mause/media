from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Orm(BaseModel):
    class Config:
        orm_mode = True


class DownloadResponse(Orm):
    id: int


class DownloadPost(Orm):
    magnet: str
    tmdb_id: int


@app.post('/download', response_model=DownloadResponse)
def download_post(download: DownloadPost):
    ...
