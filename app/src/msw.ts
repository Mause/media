import { setupServer } from 'msw/node';

export const server = setupServer();
server.events.on('request:start', ({ request }) => {
  console.log('Request start:', request.method, request.url);
});
server.events.on('request:match', ({ request }) => {
  console.log('Request match:', request.method, request.url);
});
server.events.on('request:end', ({ request }) => {
  console.log('Request end:', request.method, request.url);
});
server.events.on('request:unhandled', ({ request }) => {
  console.error('Request unhandled:', request.method, request.url);
});
