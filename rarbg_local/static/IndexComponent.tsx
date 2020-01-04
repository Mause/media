import React, { FormEvent } from 'react';
import { Component } from 'react';
import { TVShows, Movies } from './render';
import { IndexResponse, Torrents } from './streaming';
import { load } from './utils';
import { withRouter, RouteComponentProps } from 'react-router-dom';

type IndexState = { state: IndexResponse, torrents: Torrents, query: string };
type IndexProps = RouteComponentProps<{}>;

class _IndexComponent extends Component<IndexProps, IndexState> {
  interval?: number;
  constructor(props: IndexProps) {
    super(props);
    this.state = { state: { series: [], movies: [] }, torrents: {}, query: '' };
  }
  async componentDidMount() {
    this.reload();
    this.interval = setInterval(this.reload.bind(this), 1000);
  }
  async componentWillUnmount() {
    if (this.interval) {
      clearInterval(this.interval);
    }
  }
  private reload() {
    load<IndexResponse>('index', state => this.setState({ state }));
    load<Torrents>('torrents', torrents => this.setState({ torrents }));
  }
  search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    this.props.history.replace({ pathname: '/search', search: `query=${this.state.query}` })
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
      <Movies torrents={this.state.torrents} movies={this.state.state.movies} />
      <TVShows torrents={this.state.torrents} series={this.state.state.series} />
    </div >;
  }
}

const IndexComponent = withRouter(_IndexComponent);
export { IndexComponent as IndexComponent };
