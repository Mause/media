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
  return new TransformStream({
    start(controller) {
      controller.buf = '';
      controller.pos = 0;
    },
    transform(chunk, controller) {
      controller.buf += chunk;
      while (controller.pos < controller.buf.length) {
        if (controller.buf[controller.pos] == '\n') {
          const line = controller.buf.substring(0, controller.pos);
          controller.enqueue(JSON.parse(line));
          controller.buf = controller.buf.substring(controller.pos + 1);
          controller.pos = 0;
        } else {
          ++controller.pos;
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

window.onload = function () {
  const form = document.getElementById('message-form');
  const responseField = document.getElementById('response');
  let abortController = null;

  form.onsubmit = function (e) {
    e.preventDefault();

    if (abortController !== null) {
      abortController.abort();
    }

    abortController = new AbortController();

    // Retrieve the message from the textarea.
    var formData = new FormData(form);
    var message = formData.get('message');
    var body = JSON.stringify({ message });

    eventTarget = new FetchEventTarget('${__FETCH_URL__}', {
      method: 'POST',
      headers: new Headers({
        accept: 'application/json',
        'content-type': 'application/json',
      }),
      mode: 'same-origin',
      signal: abortController.signal,
      body,
    });

    eventTarget.addEventListener('tick', (event) => {
      responseField.innerHTML = JSON.stringify(event.data);
    });
  };
};
