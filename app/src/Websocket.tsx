import React, { useState, useEffect, useContext, createContext } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { DisplayTorrent, ITorrent } from './OptionsComponent';
import _ from 'lodash';
import qs from 'qs';
import io from 'socket.io-client';

const SocketContext = createContext<{ url: string | undefined }>({
  url: undefined,
});
const SocketIOProvider = SocketContext.Provider;

function useLastMessage(type: string) {
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const { url } = useContext(SocketContext);
  const socket = io(url);

  useEffect(() => {
    socket.on(type, (message) => {
      setLastMessage(message);
    });
    return () => {
      socket.off(type);
    };
  }, [type, socket]);

  return { data: lastMessage, socket };
}

function useMessages<T>(initMessage: object) {
  const { data: lastMessage, socket } = useLastMessage('message');

  useEffect(() => {
    socket.send(JSON.stringify(initMessage));
  }, [socket, initMessage]);

  const [messages, setMessages] = useState<T[]>([]);

  useEffect(() => {
    if (lastMessage) {
      setMessages((messages) =>
        messages.concat([JSON.parse(lastMessage as unknown as string) as T]),
      );
    }
  }, [lastMessage]);
  return messages;
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

  const messages = useMessages<ITorrent>(initMessage);

  return (
    <div>
      <span>{tmdbId}</span>
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

const IOWebsocket = () => (
  <SocketIOProvider
    value={{
      url: (window.location.hostname.includes('localhost')
        ? 'http://localhost:5000'
        : '') + '/ws',
    }}
  >
    <Websocket />
  </SocketIOProvider>
);

export { IOWebsocket as Websocket };
