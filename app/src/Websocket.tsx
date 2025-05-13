import { useState, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { DisplayTorrent, ITorrent } from './OptionsComponent';
import _ from 'lodash';
import qs from 'qs';
import useWebSocket, { ReadyState } from 'react-use-websocket';

function useMessages<T>(initMessage: object) {
  const url =
    (window.location.hostname.includes('localhost')
      ? 'http://localhost:5000'
      : '') + '/ws';

  const { sendMessage, lastMessage, readyState } = useWebSocket(url);

  useEffect(() => {
    sendMessage(JSON.stringify(initMessage));
  }, [sendMessage, initMessage]);

  const [messages, setMessages] = useState<T[]>([]);

  useEffect(() => {
    if (lastMessage) {
      setMessages((messages) =>
        messages.concat([JSON.parse(lastMessage as unknown as string) as T]),
      );
    }
  }, [lastMessage]);
  return { messages, readyState };
}

function Websocket() {
  const { tmdbId } = useParams<{ tmdbId: string }>();
  const { search } = useLocation();
  const query = qs.parse(search.slice(1));

  const initMessage = query.season
    ? {
        type: 'series',
        tmdb_id: tmdbId,
        season: query.season,
        episode: query.episode,
      }
    : { type: 'movie', tmdb_id: tmdbId };

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
