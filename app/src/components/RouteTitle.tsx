import type { ReactNode } from 'react';

export function RouteTitle({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <>
      <title>{title}</title>
      {children}
    </>
  );
}
