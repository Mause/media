import { useParams, useLocation } from 'react-router-dom';
import usePromise from 'react-promise-suspense';
import { useAuth0 } from '@auth0/auth0-react';
import * as _ from 'lodash-es';

import type { ITorrent } from './select/OptionsComponent';
import { getMarker, getToken } from './utils';
import type { components } from './schema';
import { DisplayTorrent, RouteTitle } from './components';
import {
  useMessages,
  readyStateToString,
  nextId,
} from './components/websocket';

type StreamRequest = components['schemas']['StreamRequest'];
type StreamArgs = StreamRequest['args'];

function get(query: URLSearchParams, key: string): number | undefined {
  const value = query.get(key);
  return value ? parseInt(value, 10) : undefined;
}

function Websocket() {
  const { tmdbId: tmdbIdS } = useParams<{ tmdbId: string }>();
  const { search } = useLocation();
  const query = new URLSearchParams(search.slice(1));
  const auth = useAuth0();
  const token = 'Bearer ' + usePromise(() => getToken(auth), []);
  const tmdbId = parseInt(tmdbIdS!, 10);

  const initMessage = (
    query.has('season')
      ? {
          type: 'series',
          tmdb_id: tmdbId,
          season: get(query, 'season') || null,
          episode: get(query, 'episode') || null,
        }
      : {
          type: 'movie',
          tmdb_id: tmdbId,
          season: null,
          episode: null,
        }
  ) satisfies StreamArgs;

  const rq = {
    jsonrpc: '2.0',
    id: nextId(),
    method: 'stream',
    authorization: token,
    args: initMessage,
  } satisfies StreamRequest;

  const { messages, readyState } = useMessages<
    { error: string; type: string } | ITorrent
  >(rq);

  const errors = messages.filter((message) => 'error' in message);
  const downloads = messages.filter(
    (message) => !('error' in message),
  ) as ITorrent[];

  return (
    <RouteTitle title="Websocket">
      <p>
        {tmdbId} -{' '}
        {query.has('season')
          ? getMarker({
              season: parseInt(query.get('season')!, 10),
              episode: query.has('episode')
                ? parseInt(query.get('episode')!, 10)
                : undefined,
            })
          : 'No season'}{' '}
        - {readyStateToString(readyState)}
      </p>
      <ul>
        <ul>
          {errors.map((message) => (
            <li key={message.error}>
              {message.type}: {message.error}
            </li>
          ))}
        </ul>
        {_.sortBy(_.uniqBy(downloads, 'download'), 'seeders').map((message) => (
          <li key={message.download}>
            <DisplayTorrent
              torrent={message}
              tmdb_id={String(tmdbId)}
              season={get(query, 'season') || undefined}
              episode={get(query, 'episode') || undefined}
            />
          </li>
        ))}
      </ul>
    </RouteTitle>
  );
}

export { Websocket };
