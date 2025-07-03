import { useState, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import usePromise from 'react-promise-suspense';
import { useAuth0 } from '@auth0/auth0-react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import * as _ from 'lodash-es';

import type { ITorrent } from './OptionsComponent';
import { getMarker, getPrefix, getToken } from './utils';
import { DisplayTorrent } from './DisplayTorrent';
import { RouteTitle } from './RouteTitle';

function useMessages<T>(initMessage: object) {
  const base = getPrefix();
  const url = `${base}/ws`;

  const { sendJsonMessage, lastJsonMessage, readyState } = useWebSocket(url);

  useEffect(() => {
    sendJsonMessage(initMessage);
  }, [sendJsonMessage, initMessage]);

  const [messages, setMessages] = useState<T[]>([]);

  useEffect(() => {
    if (lastJsonMessage) {
      setMessages((messages) => messages.concat([lastJsonMessage as T]));
    }
  }, [lastJsonMessage]);

  return { messages, readyState };
}

function Websocket() {
  const { tmdbId } = useParams<{ tmdbId: string }>();
  const { search } = useLocation();
  const query = new URLSearchParams(search.slice(1));
  const auth = useAuth0();
  const token = 'Bearer ' + usePromise(() => getToken(auth), []);

  const initMessage = query.has('season')
    ? {
        type: 'series',
        tmdb_id: tmdbId,
        season: query.get('season'),
        episode: query.get('episode'),
        authorization: token,
      }
    : {
        type: 'movie',
        tmdb_id: tmdbId,
        authorization: token,
      };

  const { messages, readyState } = useMessages<
    { error: string; type: string } | ITorrent
  >(initMessage);

  const errors = messages.filter((message) => 'error' in message);
  const downloads = messages.filter(
    (message) => !('error' in message),
  ) as ITorrent[];

  return (
    <RouteTitle title="Websocket">
      <p>{tmdbId}</p>
      <p>
        {query.has('season')
          ? getMarker({
              season: parseInt(query.get('season')!, 10),
              episode: query.has('episode')
                ? parseInt(query.get('episode')!, 10)
                : undefined,
            })
          : 'No season'}
      </p>
      <p>
        {readyState === ReadyState.CONNECTING && 'Connecting...'}
        {readyState === ReadyState.OPEN && 'Connected'}
        {readyState === ReadyState.CLOSING && 'Disconnecting...'}
        {readyState === ReadyState.CLOSED && 'Disconnected'}
        {readyState === ReadyState.UNINSTANTIATED && 'Uninstantiated'}
      </p>
      <ul>
        <ul>
          {errors.map((message) => (
            <li key={message.error}>
              {message.type}: {message.error}
            </li>
          ))}
        </ul>
        {_.uniqBy(downloads, 'download').map((message) => (
          <li key={message.download}>
            <DisplayTorrent torrent={message} tmdb_id={String(tmdbId)} />
          </li>
        ))}
      </ul>
    </RouteTitle>
  );
}

export { Websocket };
