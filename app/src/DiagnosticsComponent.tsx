import ReactLoading from 'react-loading';
import useSWR from 'swr';

export function DiagnosticsComponent() {
  const { data, isValidating } = useSWR('diagnostics');

  if (!isValidating) return <ReactLoading type="balls" color="#000" />;

  return (
    <div>
      <pre>
        <code>{JSON.stringify(data, null, 2)}</code>
      </pre>
    </div>
  );
}
