import React from 'react';
import { Component } from 'react';
import { TVShows, Movies } from './render';
import { IndexResponse, Torrents } from './streaming';
import { load } from './utils';

type IndexState = { state: IndexResponse, torrents: Torrents };

export class IndexComponent extends Component<{}, IndexState> {
  constructor(props: {}) {
    super(props);
    this.state = { state: { series: [], movies: [] }, torrents: {} };
  }
  async componentDidMount() {
    this.reload();
    setTimeout(this.reload.bind(this), 1000);
  }
  private reload() {
    load<IndexResponse>('index', state => this.setState({ state }));
    load<Torrents>('torrents', torrents => this.setState({ torrents }));
  }
  render() {
    return <div>
      <TVShows torrents={this.state.torrents} series={this.state.state.series} />
      <Movies torrents={this.state.torrents} movies={this.state.state.movies} />
    </div>;
  }
}
