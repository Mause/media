import type { ReactNode } from 'react';
import { Helmet } from 'react-helmet-async';

export function RouteTitle({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <>
      <Helmet>
        <title>{title}</title>
      </Helmet>
      {children}
    </>
  );
}
