/**
 * This file was auto-generated by swagger-to-ts.
 * Do not make direct changes to the file.
 */

export interface components {
  schemas: {
    DownloadAllResponse: {
      packs: components["schemas"]["ITorrent"][];
      complete: [string, components["schemas"]["ITorrent"][]][];
      incomplete: [string, components["schemas"]["ITorrent"][]][];
    };
    DownloadPost: {
      tmdb_id: number;
      magnet: string;
      season?: string;
      episode?: string;
    };
    DownloadSchema: {
      id: number;
      tmdb_id: number;
      transmission_id: string;
      imdb_id: string;
      type: string;
      title: string;
      timestamp: string;
      added_by: components["schemas"]["UserSchema"];
    };
    Episode: {
      name: string;
      id: number;
      episode_number: number;
      air_date?: string;
    };
    EpisodeDetailsSchema: {
      id: number;
      download: components["schemas"]["DownloadSchema"];
      show_title: string;
      season: number;
      episode?: number;
    };
    EpisodeInfo: { seasonnum?: string; epnum?: string };
    HTTPValidationError: {
      detail?: components["schemas"]["ValidationError"][];
    };
    ITorrent: {
      source: components["schemas"]["ProviderSource"];
      title: string;
      seeders: number;
      download: string;
      category: string;
      episode_info: components["schemas"]["EpisodeInfo"];
    };
    IndexResponse: {
      series: components["schemas"]["SeriesDetails"][];
      movies: components["schemas"]["MovieDetailsSchema"][];
    };
    InnerTorrent: {
      eta: number;
      hashString: string;
      id: number;
      percentDone: number;
      files: components["schemas"]["InnerTorrentFile"][];
    };
    InnerTorrentFile: { bytesCompleted: number; length: number; name: string };
    /**
     * An enumeration.
     */
    MediaType: "series" | "movie";
    MonitorGet: {
      tmdb_id: number;
      type: components["schemas"]["MonitorMediaType"];
      id: number;
      title: string;
      added_by: string;
    };
    /**
     * An enumeration.
     */
    MonitorMediaType: "MOVIE" | "TV";
    MonitorPost: {
      tmdb_id: number;
      type: components["schemas"]["MonitorMediaType"];
    };
    MovieDetailsSchema: {
      id: number;
      download: components["schemas"]["DownloadSchema"];
    };
    MovieResponse: { title: string; imdb_id: string };
    /**
     * An enumeration.
     */
    ProviderSource: "kickass" | "horriblesubs" | "rarbg";
    SearchResponse: {
      title: string;
      type: components["schemas"]["MediaType"];
      year?: number;
      imdbID: number;
      Year?: number;
      Type: components["schemas"]["MediaType"];
    };
    SeasonMeta: { episode_count: number; season_number: number };
    SeriesDetails: {
      title: string;
      imdb_id: string;
      tmdb_id: number;
      seasons: {
        [key: string]: components["schemas"]["EpisodeDetailsSchema"][];
      };
    };
    Stats: { episode?: number; movie?: number };
    StatsResponse: { user: string; values: components["schemas"]["Stats"] };
    TvResponse: {
      number_of_seasons: number;
      title: string;
      imdb_id: string;
      seasons: components["schemas"]["SeasonMeta"][];
    };
    TvSeasonResponse: { episodes: components["schemas"]["Episode"][] };
    UserSchema: { username: string; first_name: string };
    ValidationError: { loc: string[]; msg: string; type: string };
  };
}
