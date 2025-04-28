import ReactLoading from 'react-loading';
import useSWR from 'swr';

export function DiagnosticsComponent() {
  const { error, data, isValidating } = useSWR('diagnostics');

  return (
    <div>
      { isValidating && <ReactLoading type="balls" color="#000" /> }

      <pre>
        <code>{JSON.stringify({ data, error }, null, 2)}</code>
      </pre>
    </div>
  );
}
