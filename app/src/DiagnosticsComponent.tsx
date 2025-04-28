import ReactLoading from 'react-loading';
import useSWR from 'swr';
import { components } from './schema';

type HealthcheckResponse = components['schemas']['HealthcheckResponse'];

function SingleDiagnostic({ component }: { component: string }) {
  const { error, data, isValidating } = useSWR<HealthcheckResponse>(
    `diagnostics/${component}`,
  );

  return (
    <li>
      <pre>{component}: </pre>

      {isValidating && <ReactLoading type="balls" color="#000" />}

      <pre>
        <code>{JSON.stringify({ data, error }, null, 2)}</code>
      </pre>
    </li>
  );
}

export function DiagnosticsComponent() {
  const { error, data, isValidating } = useSWR<string[]>('diagnostics');

  return (
    <div>
      {isValidating && <ReactLoading type="balls" color="#000" />}

      {error && (
        <pre>
          <code>{JSON.stringify({ error }, null, 2)}</code>
        </pre>
      )}

      <ul>
        {data &&
          data.map((component) => (
            <li key={component}>
              <SingleDiagnostic component={component} />
            </li>
          ))}
      </ul>
    </div>
  );
}
