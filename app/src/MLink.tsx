import type { ReactElement, ReactNode } from 'react';
import MaterialLink from '@mui/material/Link';
import { Link } from 'react-router-dom';
import type { TypographyTypeMap } from '@mui/material';

export function MLink(
  props: {
    children: ReactNode;
    color?: TypographyTypeMap['props']['color'];
  } & Pick<Parameters<typeof Link>[0], 'to' | 'state'>,
): ReactElement {
  return <MaterialLink component={Link} {...props} underline="hover" />;
}

export function ExtMLink(props: { href: string; children: string }) {
  return (
    <MaterialLink
      href={props.href}
      target="_blank"
      rel="noopener noreferrer"
      underline="hover"
    >
      {props.children}
    </MaterialLink>
  );
}
