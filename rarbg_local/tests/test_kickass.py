from pytest import mark

from ..models import EpisodeInfo, ITorrent, ProviderSource
from ..providers.kickass import KickassProvider
from .conftest import themoviedb, tolist
from .factories import MovieResponseFactory, TvApiResponseFactory


def make(title):
    return f'''
    <div class="tab_content" id="1080">
        <table>
            <tbody>
                <tr>
                    <td><a class="torrents_table__torrent_title" href="">{title}</a></td>
                    <td><a href="magnet:aaaa">Magnet</a></td>
                    <td data-title="Seed">10</td>
                </tr>
            </tbody>
        </table>
    </div>
    '''


@mark.asyncio
async def test_tv_episode(aioresponses, clear_cache):
    themoviedb(
        aioresponses, '/tv/1', TvApiResponseFactory(name='Little Busters').dict()
    )
    aioresponses.add(
        'https://katcr.co/name/search/little-busters/i0000000/1/1',
        'GET',
        body=make('The outer limits S01E01'),
    )

    res = await tolist(KickassProvider().search_for_tv('tt0000000', 1, 1, 1))
    assert res == [
        ITorrent(
            source=ProviderSource.KICKASS,
            title='The outer limits S01E01',
            seeders=10,
            download='magnet:aaaa',
            category='TV HD Episodes',
            episode_info=EpisodeInfo(seasonnum=1, epnum=1),
        )
    ]


@mark.asyncio
async def test_tv_season(aioresponses, clear_cache):
    themoviedb(
        aioresponses, '/tv/1', TvApiResponseFactory(name='Little Busters').dict()
    )
    aioresponses.add(
        'https://katcr.co/name/little-busters/i0000000',
        'GET',
        body=make('The outer limits S01'),
    )

    res = await tolist(KickassProvider().search_for_tv('tt0000000', 1, 1))
    assert res == [
        ITorrent(
            source=ProviderSource.KICKASS,
            title='The outer limits S01',
            seeders=10,
            download='magnet:aaaa',
            category='TV HD Episodes',
            episode_info=EpisodeInfo(seasonnum=1),
        )
    ]


@mark.asyncio
async def test_movie(aioresponses, clear_cache):
    themoviedb(
        aioresponses, '/movie/1', MovieResponseFactory(title='John Flynn').dict()
    )
    aioresponses.add(
        'https://katcr.co/name/john-flynn/i0000000',
        'GET',
        body=make('The outer limits'),
    )

    res = await tolist(KickassProvider().search_for_movie('tt0000000', 1))
    assert res == [
        ITorrent(
            source=ProviderSource.KICKASS,
            title='The outer limits',
            seeders=10,
            download='magnet:aaaa',
            category='x264/1080',
        )
    ]
