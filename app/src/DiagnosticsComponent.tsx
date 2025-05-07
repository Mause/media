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
    <SimpleDiagnosticDisplay
      component={component}
      error={error}
      data={data}
      isValidating={isValidating}
    />
  );
}

export function SimpleDiagnosticDisplay({
  component,
  data,
  error,
  isValidating,
}: {
  component: string;
  data?: HealthcheckResponse[];
  error: unknown;
  isValidating: boolean;
}) {
  return (
    <li>
      {component}: {isValidating && <ReactLoading type="balls" color="#000" />}
      <ul>
        {data &&
          data.map((item, i) => (
            <li key={i}>
              <FontAwesomeIcon
                icon={faCircle}
                className={getColour(item.status)}
              />
              <pre>
                <code>
                  {JSON.stringify(
                    {
                      component_type: item.component_type,
                      time: item.time,
                      output: item.output,
                    },
                    null,
                    2,
                  )}
                </code>
              </pre>
            </li>
          ))}
      </ul>
      {error && (
        <pre>
          <code>{JSON.stringify(error, null, 2)}</code>
        </pre>
      )}
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
