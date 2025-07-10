import type { ReactElement, ReactNode } from 'react';
import MaterialLink from '@mui/material/Link';
import { NavLink, useMatch } from 'react-router-dom';
import type { TypographyTypeMap } from '@mui/material';

type Props = Parameters<typeof NavLink>[0];

export function MLink(props: {
  children: ReactNode;
  color?: TypographyTypeMap['props']['color'];
  to: Props['to'] & {};
  state: Props['state'];
}): ReactElement {
  const match = useMatch(
    typeof props.to === 'string' ? props.to : props.to.pathname!,
  );
  return (
    <MaterialLink
      component={NavLink}
      {...props}
      underline={match ? 'always' : 'hover'}
    />
  );
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
