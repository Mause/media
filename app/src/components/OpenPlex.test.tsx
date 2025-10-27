import { vi, describe, test } from 'vitest';
import userEvent from '@testing-library/user-event';
import { act, screen } from '@testing-library/react';
import { http, HttpResponse, ws } from 'msw';

import { server } from '../msw';
import { renderWithSWR } from '../test.utils';

import { OpenPlex, ContextMenu } from '.';

describe('OpenPlex', () => {
  it('should render without crashing', async () => {
    const base = 'ws://fakedomain.com:1234';
    vi.stubEnv('REACT_APP_API_PREFIX', base);

    const chat = ws.link(`${base}/ws`);
    server.use(
      chat.addEventListener('connection', async ({ client }) => {
        client.addEventListener('message', (event) => {
          console.log('Intercepted message from the client', event);
        });
      }),
    );

    const { container } = renderWithSWR(
      <ContextMenu>
        <OpenPlex
          download={{
            tmdb_id: 12345,
          }}
          type="movie"
        />
      </ContextMenu>,
    );
    expect(container).toMatchSnapshot();

    const events = userEvent.setup();

    // server.use(
    //   http.post('/api/monitor', async ({ request }) => {
    //     expect(await request.json()).toEqual({
    //       type: 'MOVIE',
    //       tmdb_id: 5,
    //     });
    //     return HttpResponse.json({});
    //   }),
    // );
    // server.use(
    //   http.get('/api/monitor', () => {
    //     return HttpResponse.json([] satisfies MonitorResponse);
    //   }),
    //   3,
    // );

    await events.click(await screen.findByTestId('context-menu-open'));
    await events.click(await screen.findByText('Open in Plex'));

    expect(container).toMatchSnapshot();
  });
});
