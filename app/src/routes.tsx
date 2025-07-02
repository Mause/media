import type { RouteObject } from 'react-router-dom';

import { RouteTitle } from './RouteTitle';
import { ParentComponentInt, SwrConfigWrapper } from './streaming';
import { Loading } from './render';

export function getRoutes() {
  return [
    {
      path: '/',
      element: (
        <SwrConfigWrapper>
          <ParentComponentInt />
        </SwrConfigWrapper>
      ),
      children: [
        {
          id: 'notFound',
          path: '*',
          element: (
            <RouteTitle title="Page not Found">
              <div>Page not found</div>
            </RouteTitle>
          ),
        },
        {
          path: '/websocket/:tmdbId',
          lazy: async () => {
            const { Websocket } = await import('./Websocket');
            return {
              Component: Websocket,
            };
          },
        },
        {
          path: '/select/:tmdb_id/options',
          lazy: async () => {
            const { MovieOptionsComponent } = await import(
              './MovieOptionsComponent'
            );
            return {
              Component: MovieOptionsComponent,
            };
          },
        },
        {
          path: '/select/:tmdb_id/season/:season/episode/:episode/options',
          lazy: async () => {
            const { TvOptionsComponent } = await import('./TvOptionsComponent');
            return {
              Component: TvOptionsComponent,
            };
          },
        },
        {
          path: '/select/:tmdb_id/season/:season/download_all',
          lazy: async () => {
            const { DownloadAllComponent } = await import(
              './DownloadAllComponent'
            );
            return {
              Component: DownloadAllComponent,
            };
          },
        },
        {
          path: '/select/:tmdb_id/season/:season',
          lazy: async () => {
            const { EpisodeSelectComponent } = await import(
              './EpisodeSelectComponent'
            );
            return {
              Component: EpisodeSelectComponent,
            };
          },
        },
        {
          path: '/select/:tmdb_id/season',
          lazy: async () => {
            const { SeasonSelectComponent } = await import(
              './SeasonSelectComponent'
            );
            return {
              Component: SeasonSelectComponent,
            };
          },
        },
        {
          path: '/search',
          lazy: async () => {
            const { SearchComponent } = await import('./SearchComponent');
            return {
              Component: SearchComponent,
            };
          },
        },
        {
          path: '/download',
          lazy: async () => {
            const { DownloadComponent } = await import('./DownloadComponent');
            return {
              Component: DownloadComponent,
            };
          },
        },
        {
          path: '/manual',
          lazy: async () => {
            const { ManualAddComponent } = await import('./ManualAddComponent');
            return {
              element: (
                <RouteTitle title="Manual">
                  <ManualAddComponent />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/stats',
          lazy: async () => {
            const { StatsComponent } = await import('./StatsComponent');
            return {
              element: (
                <RouteTitle title="Stats">
                  <StatsComponent />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/diagnostics',
          lazy: async () => {
            const { DiagnosticsComponent } = await import(
              './DiagnosticsComponent'
            );
            return {
              element: (
                <RouteTitle title="Diagnostics">
                  <DiagnosticsComponent />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/storybook',
          lazy: async () => {
            const { Storybook } = await import('./Storybook');
            return {
              element: (
                <RouteTitle title="Storybook">
                  <Storybook />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/monitor/delete/:id',
          lazy: async () => {
            const { MonitorDeleteComponent } = await import(
              './MonitorComponent'
            );
            return {
              element: (
                <RouteTitle title="Monitor">
                  <MonitorDeleteComponent />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/monitor',
          lazy: async () => {
            const { MonitorComponent } = await import('./MonitorComponent');
            return {
              element: (
                <RouteTitle title="Monitor">
                  <MonitorComponent />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/sitemap',
          lazy: async () => {
            const { SitemapRoot } = await import('./SitemapRoot');
            return { Component: SitemapRoot };
          },
        },
        {
          path: '/discover',
          hydrateFallbackElement: <Loading loading />,
          lazy: async () => {
            const { DiscoveryComponent } = await import('./DiscoveryComponent');
            return {
              element: (
                <RouteTitle title="Discover">
                  <DiscoveryComponent />
                </RouteTitle>
              ),
            };
          },
        },
        {
          path: '/',
          lazy: async () => {
            const { IndexComponent } = await import('./IndexComponent');
            return {
              element: (
                <RouteTitle title="Media">
                  <IndexComponent />
                </RouteTitle>
              ),
            };
          },
        },
      ],
    },
  ] satisfies RouteObject[];
}
