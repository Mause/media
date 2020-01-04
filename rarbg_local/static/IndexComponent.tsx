import React, { FormEvent } from 'react';
import { Component } from 'react';
import { TVShows, Movies } from './render';
import { IndexResponse, Torrents } from './streaming';
import { load } from './utils';
import { withRouter, RouteComponentProps } from 'react-router-dom';

type IndexState = { state: IndexResponse, torrents: Torrents, query: string };
type IndexProps = RouteComponentProps<{}>;

class _IndexComponent extends Component<IndexProps, IndexState> {
  constructor(props: IndexProps) {
    super(props);
    this.state = { state: { series: [], movies: [] }, torrents: {}, query: '' };
  }
  async componentDidMount() {
    this.reload();
    setTimeout(this.reload.bind(this), 1000);
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
        <label>Query:&nbsp;<input onChange={e => this.setState({ query: e.target.value })} />
        </label>
      </form>
      <TVShows torrents={this.state.torrents} series={this.state.state.series} />
      <Movies torrents={this.state.torrents} movies={this.state.state.movies} />
    </div>;
  }
}

const IndexComponent = withRouter(_IndexComponent);
export { IndexComponent as IndexComponent };
