import React, { FormEvent, useState } from 'react';
import { Component } from 'react';
import { TVShows, Movies } from './render';
import { IndexResponse, Torrents } from './streaming';
import { load } from './utils';
import { withRouter, RouteComponentProps, useHistory } from 'react-router-dom';
import qs from 'qs';

type IndexState = {
  state: IndexResponse;
  torrents?: Torrents;
  loadingTorrents: boolean;
  loadingState: boolean;
};
type IndexProps = RouteComponentProps<{}>;

class _IndexComponent extends Component<IndexProps, IndexState> {
  interval?: NodeJS.Timeout;
  constructor(props: IndexProps) {
    super(props);
    this.state = {
      state: { series: [], movies: [] },
      loadingTorrents: true,
      loadingState: true,
    };
  }
  async componentDidMount() {
    this.reload();
    this.interval = setInterval(this.reload.bind(this), 10000);
  }
  async componentWillUnmount() {
    if (this.interval) {
      clearInterval(this.interval);
    }
  }
  private reload() {
    this.setState({ loadingTorrents: true, loadingState: true });
    load<IndexResponse>('index').then(state => this.setState({ state, loadingState: false }));
    load<Torrents>('torrents').then(torrents => this.setState({ torrents, loadingTorrents: false }));
  }
  get loading() {
    return this.state.loadingState || this.state.loadingTorrents;
  }
  render() {
    return <div>
      <SearchBox />
      <Movies torrents={this.state.torrents} movies={this.state.state.movies} loading={this.loading} />
      <TVShows torrents={this.state.torrents} series={this.state.state.series} loading={this.loading} />
    </div >;
  }
}

export function SearchBox() {
  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    history.push({ pathname: '/search', search: qs.stringify({ query }) });
  }

  const [query, setQuery] = useState('');
  const history = useHistory();

  return (
    <form onSubmit={search}>
      <input name="query" onChange={e => setQuery(e.target.value)} />
      &nbsp;
      <input type="submit" value="Search" />
    </form>
  );
}

const IndexComponent = withRouter(_IndexComponent);
export { IndexComponent };
