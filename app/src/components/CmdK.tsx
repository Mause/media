import {
  Link,
} from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import * as _ from 'lodash-es';
import CommandPalette, {
  filterItems,
  getItemIndex,
  useHandleOpenCommandPalette,
} from 'react-cmdk';
import { useState } from 'react';

import 'react-cmdk/dist/cmdk.css';

export function CmdK() {
  const { loginWithRedirect, isAuthenticated, logout } = useAuth0();
  const [page, setPage] = useState<'root' | 'search'>('root');
  const [open, setOpen] = useState<boolean>(false);
  const [search, setSearch] = useState('');

  useHandleOpenCommandPalette(setOpen);

  const external = {
    target: '_blank',
    rel: 'noopener noreferrer',
  };

  const filteredItems = filterItems(
    [
      {
        heading: 'Home',
        id: 'home',
        items: [
          {
            id: 'home',
            children: 'Home',
            icon: 'HomeIcon',
            href: '/',
          },
          {
            id: 'monitors',
            children: 'Monitors',
            icon: 'EyeIcon',
            href: '/monitors',
          },
          {
            id: 'transmission',
            children: 'Transmission',
            icon: 'RadioIcon',
            href: 'http://novell.mause.me:9091',
            ...external,
          },
          {
            id: 'plex',
            children: 'Plex',
            icon: 'PlayIcon',
            href: 'https://app.plex.tv',
            ...external,
          },
          {
            id: 'discover',
            children: 'Discover',
            icon: 'MagnifyingGlassIcon',
            href: '/discover',
          },
          /*
          {
            id: 'settings',
            children: 'Settings',
            icon: 'CogIcon',
            href: '#',
          },
          */
          {
            id: 'search',
            children: 'Search',
            icon: 'MagnifyingGlassIcon',
            closeOnSelect: false,
            onClick: () => {
              setPage('search');
            },
          },
        ],
      },
      {
        heading: 'Other',
        id: 'advanced',
        items: [
          {
            id: 'diagnostics',
            children: 'Diagnostics',
            icon: 'CodeBracketIcon',
            href: '/diagnostics',
          },
          /*
          {
            id: 'privacy-policy',
            children: 'Privacy policy',
            icon: 'LifebuoyIcon',
            href: '#',
          },
          */
          {
            id: 'log-out',
            children: isAuthenticated ? 'Logout' : 'Login',
            icon: 'ArrowRightOnRectangleIcon',
            onClick: () => {
              if (isAuthenticated) {
                void loginWithRedirect({});
              } else {
                void logout();
              }
            },
          },
        ],
      },
    ],
    search,
  );

  return (
    <CommandPalette
      onChangeSearch={setSearch}
      onChangeOpen={setOpen}
      search={search}
      isOpen={open}
      page={page}
      renderLink={({ href, ...rest }) =>
        href!.startsWith('http') ? (
          <a href={href} {...rest} />
        ) : (
          <Link to={href!} {...rest} />
        )
      }
    >
      <CommandPalette.Page id="root">
        {filteredItems.length ? (
          filteredItems.map((list) => (
            <CommandPalette.List key={list.id} heading={list.heading}>
              {list.items.map(({ id, ...rest }) => (
                <CommandPalette.ListItem
                  key={id}
                  index={getItemIndex(filteredItems, id)}
                  {...rest}
                />
              ))}
            </CommandPalette.List>
          ))
        ) : (
          <CommandPalette.FreeSearchAction />
        )}
      </CommandPalette.Page>

      <CommandPalette.Page
        searchPrefix={['Search']}
        id="search"
        onEscape={() => {
          setPage('root');
        }}
      >
        <CommandPalette.List heading="Results">
          <CommandPalette.ListItem index={0}>
            Nothing here
          </CommandPalette.ListItem>
        </CommandPalette.List>
      </CommandPalette.Page>
    </CommandPalette>
  );
};
