import { MenuItem } from '@mui/material';

export function OpenIMDB({ download }: { download: { imdb_id: string } }) {
  return (
    <MenuItem
      component="a"
      href={`https://www.imdb.com/title/${download.imdb_id}`}
      target="_blank"
    >
      Open in IMDB
    </MenuItem>
  );
}
