import React, { FormEvent } from 'react';
import { Component } from 'react';
import { TVShows, Movies } from './render';
import { IndexResponse, Torrents } from './streaming';
import { load } from './utils';
import { withRouter, RouteComponentProps } from 'react-router-dom';

type IndexState = { state: IndexResponse, torrents?: Torrents, query: string, loadingTorrents: boolean, loadingState: boolean };
type IndexProps = RouteComponentProps<{}>;

class _IndexComponent extends Component<IndexProps, IndexState> {
  interval?: number;
  constructor(props: IndexProps) {
    super(props);
    this.state = { state: { series: [], movies: [] }, query: '', loadingTorrents: true, loadingState: true };
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
    load<IndexResponse>('index', state => this.setState({ state, loadingState: false }));
    load<Torrents>('torrents', torrents => this.setState({ torrents, loadingTorrents: false }));
  }
  search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    this.props.history.replace({ pathname: '/search', search: `query=${this.state.query}` })
  }
  get loading() {
    return this.state.loadingState || this.state.loadingTorrents;
  }
  render() {
    return <div>
      <form onSubmit={this.search.bind(this)}>
        <label>
          <strong>Query</strong>&nbsp;
          <input onChange={e => this.setState({ query: e.target.value })} />&nbsp;
          <input type="submit" value="Search"></input>
        </label>
      </form>
      <Movies torrents={this.state.torrents} movies={this.state.state.movies} loading={this.loading} />
      <TVShows torrents={this.state.torrents} series={this.state.state.series} loading={this.loading} />
    </div >;
  }
}

const IndexComponent = withRouter(_IndexComponent);
export { IndexComponent as IndexComponent };
