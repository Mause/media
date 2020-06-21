import { useEffect, useState } from 'react';

export const CallbackMountPoint: { onAppUpdate?: () => void } = {};

export function useAppUpdated() {
  const [appUpdated, setAppUpdated] = useState(false);
  useEffect(() => {
    CallbackMountPoint.onAppUpdate = () => {
      setAppUpdated(true);
    };
    return () => {
      CallbackMountPoint.onAppUpdate = undefined;
    };
  });
  return appUpdated;
}

export function appUpdated() {
  CallbackMountPoint.onAppUpdate && CallbackMountPoint.onAppUpdate();
}
