import { Component } from 'react';
import { RouteComponentProps, Link, withRouter } from 'react-router-dom';
import { load } from './utils';
import _ from 'lodash';
import React from 'react';
import ReactLoading from 'react-loading';

type Props = RouteComponentProps<{ tmdb_id: string }>;
interface TV {
  number_of_seasons: number;
}

class _SeasonSelectComponent extends Component<Props, { tv?: TV, loading: boolean }>{
  constructor(props: Props) {
    super(props);
    this.state = { tv: undefined, loading: true }
  }

  componentDidMount() {
    load<TV>(`tv/${this.props.match.params.tmdb_id}`).then(tv => this.setState({ tv }))
  }

  render() {
    return <div>
      {!this.state.tv ?
        <ReactLoading type='balls' color='#000000' /> :
        <ul>
          {_.range(1, this.state.tv.number_of_seasons + 1).map(i =>
            <li key={i}>
              <Link to={`/select/${this.props.match.params.tmdb_id}/season/${i}`}>
                Season {i}
              </Link>
            </li>
          )}
        </ul>
      }
    </div>
  }
}
interface Episode {
  episode_number: number;
  id: string;
  name: string;
}
export interface Season {
  episodes: Episode[];
}
type EpisodeProps = RouteComponentProps<{ tmdb_id: string, season: string }>;
class _EpisodeSelectComponent extends Component<EpisodeProps, { season?: Season }> {
  constructor(props: EpisodeProps) {
    super(props);
    this.state = { season: undefined }
  }

  componentDidMount() {
    const { tmdb_id, season } = this.props.match.params;
    load<Season>(`tv/${tmdb_id}/season/${season}`).then(season => this.setState({ season }));
  }

  render() {
    const { tmdb_id, season } = this.props.match.params;
    return <div>
      {this.state.season ? <ol>
        {this.state.season.episodes.map(episode =>
          <li key={episode.id} value={episode.episode_number}>
            <Link to={`/select/${tmdb_id}/season/${season}/episode/${episode.episode_number}/options`}>
              {episode.name}
            </Link>
          </li>
        )}
      </ol> : <ReactLoading type='balls' color='#000' />}
      <a href={`/select/${tmdb_id}/season/${season}/download_all`}>Download season</a>
    </div>;
  }
}

const EpisodeSelectComponent = withRouter(_EpisodeSelectComponent);
const SeasonSelectComponent = withRouter(_SeasonSelectComponent);

export { SeasonSelectComponent, EpisodeSelectComponent };
