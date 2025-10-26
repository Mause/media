import { OpenPlex, ContextMenu } from '.';
import { describe, test } from 'vitest';
import { renderWithSWR } from '../test.utils';
import userEvent from '@testing-library/user-event';
import { act, screen } from '@testing-library/react';
import { server } from '../msw';
import { http, HttpResponse } from 'msw';

describe('OpenPlex', () => {
  test('should render without crashing', async () => {
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
