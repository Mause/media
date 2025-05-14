import { useState, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { DisplayTorrent, ITorrent } from './OptionsComponent';
import _ from 'lodash';
import qs from 'qs';
import usePromise from 'react-promise-suspense';
import { useAuth0 } from '@auth0/auth0-react';
import useWebSocket, { ReadyState } from 'react-use-websocket';

function useMessages<T>(initMessage: object) {
  const prefix = process.env.REACT_APP_API_PREFIX;

  let base = '';
  if (prefix) {
    base = `https://${prefix}`;
  } else if (window.location.host.includes('localhost')) {
    base = 'http://localhost:5000';
  }
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
  const query = qs.parse(search.slice(1));
  const auth = useAuth0();
  const token = "Bearer " + usePromise(auth.getAccessTokenSilently, [{}]);

  const initMessage = query.season
    ? {
        type: 'series',
        tmdb_id: tmdbId,
        season: query.season,
        episode: query.episode,
        authorization: token,
      }
    : {
        type: 'movie',
        tmdb_id: tmdbId,
        authorization: token,
      };

  const { messages, readyState } = useMessages<ITorrent>(initMessage);

  return (
    <div>
      <span>{tmdbId}</span>
      <span>{String(query?.season)}</span>
      <span>{String(query?.episode)}</span>
      <span>
        {readyState === ReadyState.CONNECTING && 'Connecting...'}
        {readyState === ReadyState.OPEN && 'Connected'}
        {readyState === ReadyState.CLOSING && 'Disconnecting...'}
        {readyState === ReadyState.CLOSED && 'Disconnected'}
        {readyState === ReadyState.UNINSTANTIATED && 'Uninstantiated'}
      </span>
      <ul>
        {_.uniqBy(messages, 'download').map((message) => (
          <li key={message.download}>
            <DisplayTorrent torrent={message} tmdb_id={String(tmdbId)} />
          </li>
        ))}
      </ul>
    </div>
  );
}

export { Websocket };
