import type { RouteConfig } from '@react-router/dev/routes';

export default [
  {
    path: '/',
    file: './ParentComponent.tsx',
    children: [
      {
        path: '/websocket/:tmdbId',
        file: './Websocket.tsx',
      },
      {
        path: '/select/:tmdb_id/options',
        file: './select/MovieOptionsComponent.tsx',
      },

      {
        path: '/select/:tmdb_id/season/:season/episode/:episode/options',
        file: './select/EpisodeOptionsComponent.tsx',
      },
      {
        path: '/select/:tmdb_id/season/:season/download_all',
        file: './select/DownloadAllComponent.tsx',
      },
      {
        path: '/select/:tmdb_id/season/:season',
        file: './select/EpisodeSelectComponent.tsx',
      },
      {
        path: '/select/:tmdb_id/season',
        file: './select/SeasonSelectComponent.tsx',
      },
      {
        path: '/search',
        file: './SearchComponent.tsx',
      },
      {
        path: '/download',
        file: './DownloadComponent.tsx',
      },
      {
        path: '/manual',
        file: './ManualAddComponent.tsx',
      },
      {
        path: '/stats',
        file: './StatsComponent.tsx',
      },
      {
        path: '/diagnostics',
        file: './DiagnosticsComponent.tsx',
      },
      {
        path: '/storybook',
        file: './Storybook.tsx',
      },
      {
        path: '/monitor/delete/:id',
        file: './MonitorDeleteComponent.tsx',
      },
      {
        path: '/monitor',
        file: './MonitorComponent.tsx',
      },
      {
        path: '/sitemap',
        file: './SitemapRoot.tsx',
      },
      {
        path: '/discover',
        file: './DiscoveryComponent.tsx',
      },
      {
        path: '/',
        file: './IndexComponent.tsx',
      },
    ],
  },
] satisfies RouteConfig;
