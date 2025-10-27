import { useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import _ from 'lodash-es';
import usePromise from 'react-promise-suspense';
import MenuItem from '@mui/material/MenuItem';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContentText from '@mui/material/DialogContentText';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';

import { getToken } from '../utils';
import type { components } from '../schema';

import { OpenNewWindow } from './OpenNewWindow';
import { nextId, readyStateToString, useMessage } from './websocket';

type PlexRootResponse = components['schemas']['PlexRootResponse'];
type PlexRequest = components['schemas']['PlexRequest'];

export function OpenPlex({
  download,
  type,
}: {
  download: { tmdb_id: number };
  type: 'movie' | 'tv';
}) {
  const auth = useAuth0();
  const [open, setOpen] = useState(false);
  const token = 'Bearer ' + usePromise(() => getToken(auth), []);
  const { message, trigger, readyState, state } = useMessage<
    PlexRequest,
    PlexRootResponse
  >({
    method: 'plex',
    jsonrpc: '2.0',
    id: nextId(),
    authorization: token,
    params: {
      tmdb_id: download.tmdb_id,
      media_type: type,
    },
  });

  if (message) {
    const first = _.values(message.result).find((v) => v)!;
    return <OpenNewWindow link={first.link} label={first.item.title} />;
  }

  return (
    <>
      <Dialog open={open}>
        <DialogTitle>Search plex for media...</DialogTitle>
        <DialogContent>
          <DialogContentText>
            {readyStateToString(readyState)}
            <br />
            {state}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>
      <MenuItem
        onClick={() => {
          setOpen(true);
          trigger();
        }}
      >
        <span className="unselectable">Open in Plex</span>
      </MenuItem>
    </>
  );
}
