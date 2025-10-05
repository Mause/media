import { useState, useEffect, useMemo } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';

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

export function useMessage<REQ extends BaseRequest, T>(request: REQ) {
  const base = getPrefix();
  const url = `${base}/ws`;

  const { sendJsonMessage, lastJsonMessage, readyState } = useWebSocket(url);
  const trigger = useMemo(
    () => () => {
      sendJsonMessage(request);
    },
    [sendJsonMessage, request],
  );

  const [message, setMessage] = useState<T | null>(null);
  useEffect(() => {
    if (lastJsonMessage) {
      setMessage(lastJsonMessage as T);
    }
  }, [lastJsonMessage]);

  return { message, trigger, readyState };
}

export function readyStateToString(readyState: ReadyState) {
  switch (readyState) {
    case ReadyState.CONNECTING:
      return 'Connecting...';
    case ReadyState.OPEN:
      return 'Connected';
    case ReadyState.CLOSING:
      return 'Disconnecting...';
    case ReadyState.CLOSED:
      return 'Disconnected';
    case ReadyState.UNINSTANTIATED:
      return 'Uninstantiated';
    default:
      return 'Unknown';
  }
}
