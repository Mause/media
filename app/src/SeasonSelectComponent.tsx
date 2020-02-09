import { RouteComponentProps, Link, withRouter } from 'react-router-dom';
import { useLoad } from './utils';
import _ from 'lodash';
import React from 'react';
import ReactLoading from 'react-loading';

type Props = RouteComponentProps<{ tmdb_id: string }>;
export interface TV {
  number_of_seasons: number;
  title: string;
  seasons: { episode_count: number }[];
}

function _SeasonSelectComponent(props: Props) {
  const tv = useLoad<TV>(`tv/${props.match.params.tmdb_id}`);

  return <div>
    <h3>{tv && tv.title}</h3>
    {!tv ?
      <ReactLoading type='balls' color='#000000' /> :
      <ul>
        {_.range(1, tv.number_of_seasons + 1).map(i =>
          <li key={i}>
            <Link to={`/select/${props.match.params.tmdb_id}/season/${i}`}>
              Season {i}
            </Link>
          </li>
        )}
      </ul>
    }
  </div>;
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
function _EpisodeSelectComponent(props: EpisodeProps) {
  const { tmdb_id, season: seasonNumber } = props.match.params;
  const season = useLoad<Season>(`tv/${tmdb_id}/season/${seasonNumber}`)

  return <div>
    <h3>Season {seasonNumber}</h3>
    <Link to={`/select/${tmdb_id}/season`}><small>Back to seasons</small></Link>
    {season ? <ol>
      {season.episodes.map(episode =>
        <li key={episode.id} value={episode.episode_number}>
          <Link to={`/select/${tmdb_id}/season/${seasonNumber}/episode/${episode.episode_number}/options`}>
            {episode.name}
          </Link>
        </li>
      )}
    </ol> : <ReactLoading type='balls' color='#000' />}
    <a href={`/select/${tmdb_id}/season/${seasonNumber}/download_all`}>Download season</a>
    <br />
  </div>;
}

const EpisodeSelectComponent = withRouter(_EpisodeSelectComponent);
const SeasonSelectComponent = withRouter(_SeasonSelectComponent);

export { SeasonSelectComponent, EpisodeSelectComponent };
