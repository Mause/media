from ..models import EpisodeInfo, ITorrent
from ..providers import KickassProvider, ProviderSource
from .conftest import themoviedb
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


def test_tv_episode(responses, clear_cache):
    themoviedb(responses, '/tv/1', TvApiResponseFactory(name='Little Busters').dict())
    responses.add(
        'GET',
        'https://katcr.co/name/search/little-busters/i0000000/1/1',
        make('The outer limits S01E01'),
    )

    res = list(KickassProvider().search_for_tv('tt0000000', 1, 1, 1))
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


def test_tv_season(responses, clear_cache):
    themoviedb(responses, '/tv/1', TvApiResponseFactory(name='Little Busters').dict())
    responses.add(
        'GET',
        'https://katcr.co/name/little-busters/i0000000',
        make('The outer limits S01'),
    )

    res = list(KickassProvider().search_for_tv('tt0000000', 1, 1))
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


def test_movie(responses, clear_cache):
    themoviedb(responses, '/movie/1', MovieResponseFactory(title='John Flynn').dict())
    responses.add(
        'GET', 'https://katcr.co/name/john-flynn/i0000000', make('The outer limits')
    )

    res = list(KickassProvider().search_for_movie('tt0000000', 1))
    assert res == [
        ITorrent(
            source=ProviderSource.KICKASS,
            title='The outer limits',
            seeders=10,
            download='magnet:aaaa',
            category='x264/1080',
            episode_info=EpisodeInfo(),
        )
    ]