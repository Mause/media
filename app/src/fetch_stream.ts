function makeWriteableEventStream(eventTarget: EventTarget) {
  return new WritableStream({
    start() {
      eventTarget.dispatchEvent(new Event('start'));
    },
    write(message: unknown) {
      eventTarget.dispatchEvent(new MessageEvent('message', { data: message }));
    },
    close() {
      eventTarget.dispatchEvent(new CloseEvent('close'));
    },
    abort(reason: string) {
      eventTarget.dispatchEvent(new CloseEvent('abort', { reason }));
    },
  });
}

function makeJsonDecoder() {
  let buf = '',
    pos = 0;
  return new TransformStream({
    start() {
      buf = '';
      pos = 0;
    },
    transform(chunk, controller) {
      buf += chunk;
      while (pos < buf.length) {
        if (buf[pos] === '\n') {
          const line = buf.substring(5, pos); // 5 to strip data: prefix
          if (line.trim().length) {
            controller.enqueue(JSON.parse(line));
          }
          buf = buf.substring(pos + 2); // 2 for 2 newlines
          pos = 0;
        } else {
          ++pos;
        }
      }
    },
  });
}

export function FetchEventTarget(url: string, init: RequestInit) {
  const eventTarget = new EventTarget();
  const jsonDecoder = makeJsonDecoder();
  const eventStream = makeWriteableEventStream(eventTarget);
  fetch(url, init)
    .then((response) =>
      response
        .body!.pipeThrough(new TextDecoderStream())
        .pipeThrough(jsonDecoder)
        .pipeTo(eventStream),
    )
    .catch((error: unknown) => {
      eventTarget.dispatchEvent(
        new CustomEvent('error', { detail: error as Error }),
      );
    });
  return eventTarget;
}
