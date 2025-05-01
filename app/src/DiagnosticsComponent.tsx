import ReactLoading from 'react-loading';
import useSWR from 'swr';
import { components } from './schema';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircle } from '@fortawesome/free-solid-svg-icons';

type HealthcheckResponse = components['schemas']['HealthcheckResponse'];

function getColour(status?: HealthcheckResponse['status']) {
  switch (status) {
    case 'pass':
      return 'green';
    case 'warn':
      return 'yellow';
    case 'fail':
      return 'red';
    default:
      return 'grey';
  }
}

function SingleDiagnostic({ component }: { component: string }) {
  const { error, data, isValidating } = useSWR<HealthcheckResponse[]>(
    `diagnostics/${component}`,
  );

  return (
    <li>
      <FontAwesomeIcon
        icon={faCircle}
        className={getColour(data && data[0]?.status)}
      />
      <pre>{component}: </pre>

      {isValidating && <ReactLoading type="balls" color="#000" />}

      <pre>
        <code>{JSON.stringify(error ?? data, null, 2)}</code>
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
