import type { RouteObject } from 'react-router-dom';

import { ParentComponentInt } from './streaming';

export function getRoutes() {
  return [
    {
      path: '/',
      Component: ParentComponentInt,
      children: [
        {
          id: 'notFound',
          path: '*',
          lazy: async () => {
            const { FourOhFour } = await import('./catchall');
            return {
              Component: FourOhFour,
            };
          },
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
              Component: ManualAddComponent,
            };
          },
        },
        {
          path: '/stats',
          lazy: async () => {
            const { StatsComponent } = await import('./StatsComponent');
            return {
              Component: StatsComponent,
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
              Component: DiagnosticsComponent,
            };
          },
        },
        {
          path: '/storybook',
          lazy: async () => {
            const { Storybook } = await import('./Storybook');
            return {
              Component: Storybook,
            };
          },
        },
        {
          path: '/monitor/delete/:id',
          lazy: async () => {
            const { MonitorDeleteComponent } = await import(
              './MonitorDeleteComponent'
            );
            return {
              Component: MonitorDeleteComponent,
            };
          },
        },
        {
          path: '/monitor',
          lazy: async () => {
            const { MonitorComponent } = await import('./MonitorComponent');
            return {
              Component: MonitorComponent,
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
          lazy: async () => {
            const { DiscoveryComponent } = await import('./DiscoveryComponent');
            return {
              Component: DiscoveryComponent,
            };
          },
        },
        {
          path: '/',
          lazy: async () => {
            const { IndexComponent } = await import('./IndexComponent');
            return {
              Component: IndexComponent,
            };
          },
        },
      ],
    },
  ] satisfies RouteObject[];
}
