import Alert from '@mui/material/Alert';
import get from 'lodash/get';

export function DisplayError(props: { error: Error; message?: string }) {
  const message =
    get(props.error, 'response.data.message') ||
    (props.message || 'Unable to connect to transmission') +
      ': ' +
      props.error.toString();

  return (
    <div>
      <br />
      <Alert color="warning">
        <span data-testid="errorMessage">{message}</span>
      </Alert>
    </div>
  );
}
