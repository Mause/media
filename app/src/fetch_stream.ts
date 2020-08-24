function makeWriteableEventStream(eventTarget) {
  return new WritableStream({
    start(controller) {
      eventTarget.dispatchEvent(new Event('start'));
    },
    write(message, controller) {
      eventTarget.dispatchEvent(
        new MessageEvent(message.type, { data: message.data }),
      );
    },
    close(controller) {
      eventTarget.dispatchEvent(new CloseEvent('close'));
    },
    abort(reason) {
      eventTarget.dispatchEvent(new CloseEvent('abort', { reason }));
    },
  });
}

function makeJsonDecoder() {
  let buf = '',
    pos = 0;
  return new TransformStream({
    start(controller) {
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

function FetchEventTarget(input, init) {
  const eventTarget = new EventTarget();
  const textDecoder = new TextDecoder('utf-8');
  const jsonDecoder = makeJsonDecoder(input);
  const eventStream = makeWriteableEventStream(eventTarget);
  fetch(input, init)
    .then((response) => {
      response.body
        .pipeThrough(new TextDecoderStream())
        .pipeThrough(jsonDecoder)
        .pipeTo(eventStream);
    })
    .catch((error) => {
      eventTarget.dispatchEvent(new CustomEvent('error', { detail: error }));
    });
  return eventTarget;
}
