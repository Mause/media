import { faSpinner } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

export function Loading({
  loading,
  large,
}: {
  loading: boolean;
  large?: boolean;
}) {
  return loading ? (
    <FontAwesomeIcon
      spin={true}
      icon={faSpinner}
      size={large ? undefined : 'xs'}
    />
  ) : (
    <></>
  );
}
