import type { RouteObject } from 'react-router-dom';

import { RouteTitle } from './RouteTitle';
import { MLink } from './MLink';
import { getRoutes } from './routes';

export function SitemapRoot() {
  return (
    <RouteTitle title="Sitemap">
      <Sitemap routes={getRoutes()} />
    </RouteTitle>
  );
}
function Sitemap({ routes }: { routes: RouteObject[] }) {
  return (
    <ul>
      {routes.map((route) => (
        <li key={route.path}>
          <MLink to={route.path!}>{route.path}</MLink>
          {route.children ? <Sitemap routes={route.children} /> : undefined}
        </li>
      ))}
    </ul>
  );
}
