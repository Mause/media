import { useState, useEffect } from 'react';
import useWebSocket from 'react-use-websocket';

import { getPrefix } from '../utils';
import type { components } from '../schema';

type BaseRequest = components['schemas']['BaseRequest'];

export function useMessages<T>(initMessage: BaseRequest) {
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
