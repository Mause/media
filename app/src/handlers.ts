import { http, HttpResponse } from 'msw'
import { Monitor } from './MonitorComponent'

export const handlers = [
	http.get('/api/hello', () => {
		return HttpResponse.json({ message: 'Hello World!' })
	}

		)
		,
	http.get('/api/monitor', () => {



    const res: Monitor[] = [
      {
        id: 1,
        title: 'Hello World',
        tmdb_id: 5,
        type: 'MOVIE',
        added_by: 'me',
      },
    ];
    return HttpResponse.json(res)
	})
]
