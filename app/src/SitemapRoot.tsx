import type { RouteObject } from 'react-router-dom';

import { RouteTitle, MLink } from './components';
import routes from './routes';

export default function SitemapRoot() {
  return (
    <RouteTitle title="Sitemap">
      <Sitemap routes={routes} />
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
