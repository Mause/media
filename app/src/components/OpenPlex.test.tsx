import { it, vi, describe } from 'vitest';
import userEvent from '@testing-library/user-event';
import { screen } from '@testing-library/react';
import { ws } from 'msw';
import { act } from 'react';

import { server } from '../msw';
import { renderWithSWR, timeout } from '../test.utils';

import { OpenPlex, ContextMenu } from '.';
import { components } from '../schema';
import { Lock } from './Lock';

type PlexRootResponse = components['schemas']['PlexRootResponse'];
type PlexRequest = components['schemas']['PlexRequest'];

describe('OpenPlex', () => {
  it('should render without crashing', async () => {
    const base = 'ws://fakedomain.com:1234';
    vi.stubEnv('REACT_APP_API_PREFIX', base);

    const lock = new Lock();

    const chat = ws.link(`${base}/ws`);
    server.use(
      chat.addEventListener('connection', ({ client }) => {
        console.log('Client connected to fake WebSocket server');
        client.addEventListener('message', (event) => {
          console.log('Intercepted message from the client', event);
          const req: PlexRequest = JSON.parse(event.data.toString());
          client.send(
            JSON.stringify({
              id: req.id,
              jsonrpc: '2.0',
              result: {
                imdb: {
                  // @ts-expect-error we dont use this field
                  item: {},
                  link: 'http://plex.tv/web/app#!/server/fake-server-id/details?key=%2Flibrary%2Fmetadata%2F12345',
                  title: 'Fake Movie Title',
                  type: 'movie',
                },
              },
            } satisfies PlexRootResponse),
          );
          lock.release();
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
    expect(container).toMatchSnapshot();

    await events.click(await screen.findByText('Open in Plex'));
    const dialog = await screen.findByTestId('plex-dialog');
    expect(dialog).toMatchSnapshot();

    await act(async () => {
      await timeout(1000, lock.wait());
    });
    expect(dialog).toMatchSnapshot();
  });
});
