import { useState, useEffect, useMemo } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import * as Sentry from '@sentry/react';

import { getPrefix } from '../utils';
import type { components } from '../schema';

type BaseRequest = components['schemas']['BaseRequest'];
type SuccessResult = components['schemas']['SuccessResult'];
type ErrorResult = components['schemas']['ErrorResult'];

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

export function useMessage<REQ extends BaseRequest, T extends SuccessResult>(
  request: REQ,
) {
  const base = getPrefix();
  const url = `${base}/ws`;
  const [state, setState] = useState<string>('idle');
  const [responseError, setResponseError] = useState<
    ErrorResult['error'] | null
  >(null);

  const { sendJsonMessage, lastJsonMessage, readyState } = useWebSocket(url);
  const trigger = useMemo(
    () => () => {
      setState('sending');
      sendJsonMessage(request);
    },
    [sendJsonMessage, request],
  );

  const [message, setMessage] = useState<T | null>(null);
  useEffect(() => {
    if (lastJsonMessage) {
      if ((lastJsonMessage as T).id === request.id) {
        if ('error' in (lastJsonMessage as ErrorResult)) {
          const error = (lastJsonMessage as ErrorResult).error;
          setState('error');
          setResponseError(error);
          console.error('Error message', error);
          Sentry.captureException(new Error(error.message), {
            extra: error,
          });
        } else {
          setState('received');
          setMessage(lastJsonMessage as T);
        }
      } else if ((lastJsonMessage as T).id === -1) {
        console.log('Got notification', lastJsonMessage);
      } else {
        console.error('Unexpected message', lastJsonMessage);
      }
    }
  }, [lastJsonMessage]);

  return { message, trigger, state, readyState, error: responseError };
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

let id = 0;
export function nextId(): number {
  return id++;
}
