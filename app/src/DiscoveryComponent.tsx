import type { LoaderFunction } from 'react-router-dom';
import { useLoaderData } from 'react-router-dom';

export const loader = ((): { message: string } => {
  const data = {
    message: 'Discovery component loaded successfully',
  };
  return data;
}) satisfies LoaderFunction;

export function DiscoveryComponent() {
  const data = useLoaderData<typeof loader>();
  return (
    <div>
      <h1>Discovery Component</h1>
      <p>This is a placeholder for the Discovery component.</p>
      <p>{data?.message}</p>
    </div>
  );
}
