import React, { useState, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { DisplayTorrent, ITorrent } from './OptionsComponent';
import _ from 'lodash';
import qs from 'qs';
import { useLastMessage, SocketIOProvider } from 'use-socketio';

function useMessages<T>(initMessage: object) {
  const { data: lastMessage, socket } = useLastMessage('message');

  useEffect(
    () => {
      socket.send(JSON.stringify(initMessage));
    },
    [socket, initMessage],
  );

  const [messages, setMessages] = useState<T[]>([]);

  useEffect(
    () => {
      if (lastMessage) {
        setMessages(messages =>
          messages.concat([JSON.parse(lastMessage) as T]),
        );
      }
    },
    [lastMessage],
  );
  return messages;
}

function Websocket() {
  const { tmdbId } = useParams();
  const { search } = useLocation();
  const query = qs.parse(search);

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
        {_.uniqBy(messages, 'download').map(message => (
          <li key={message.download}>
            <DisplayTorrent torrent={message} tmdb_id={String(tmdbId)} />
          </li>
        ))}
      </ul>
    </div>
  );
}

const IOWebsocket = () => (
  <SocketIOProvider url="http://localhost:5000">
    <Websocket />
  </SocketIOProvider>
);

export { IOWebsocket as Websocket };
