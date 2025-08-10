// rustimport:pyo3
use pyo3::prelude::*;
use yts_api::Movie;

#[pyclass(get_all)]
#[derive(Debug)]
struct ITorrent {
    hash: String,
    seeders: u32,
    leechers: i32,
    name: String,
}

#[pymethods]
impl ITorrent {
    fn __repr__(&self) -> String {
        format!("{self:?}")
    }
}

#[pyfunction]
pub(crate) fn search_leetx(py: Python, term: String) -> Result<Bound<'_, PyAny>, PyErr> {
    pyo3_async_runtimes::tokio::future_into_py(py, async move {
        torrent_search::search_l337x(term)
        .await
        .map(|list| {
                list.into_iter()
                .map(|movie| ITorrent {
                    name: movie.name,
                    leechers: movie.leeches.unwrap_or(0) as i32,
                    seeders: movie.seeders.unwrap_or(0),
                    hash: movie.magnet.unwrap_or("".to_string()),
                })
                .collect::<Vec<ITorrent>>()
        })
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Error: {e}")))
    })
}

#[pyfunction]
pub fn search_yts(py: Python, term: String) -> Result<Bound<'_, PyAny>, PyErr> {
    pyo3_async_runtimes::tokio::future_into_py(py, async move {
        yts_api::ListMovies::new()
            .query_term(&term.replace(" ", "+"))
            .limit(50)
        .execute()
        .await
        .map(|list| {
            let vec = list.movies.iter().filter(|movie| movie.imdb_code == term).collect::<Vec<&Movie>>();
            vec.first()
                .map(|movie| movie.torrents.iter()
                .map(|movie| ITorrent {
                    hash: movie.hash.clone(),
                    seeders: movie.seeds,
                    leechers: -1, // movie.peers - movie.seeds,
                    name: movie.quality.clone()
                })
                .collect::<Vec<ITorrent>>())
        })
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Error: {e}")))
    })
}

#[pymodule]
fn attractive(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(search_yts, m)?)?;
    m.add_function(wrap_pyfunction!(search_leetx, m)?)?;
    m.add_class::<ITorrent>()?;
    Ok(())
}
