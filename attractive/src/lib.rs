// rustimport:pyo3
use pyo3::prelude::*;
use yts_api::Movie;

#[pyclass(get_all)]
#[derive(Debug)]
struct PyMovie {
    hash: String,
    seeders: u32,
    leechers: u32,
    name: String,
}

#[pymethods]
impl PyMovie {
    fn __repr__(&self) -> String {
        format!("{self:?}")
    }
}

#[pyclass(get_all)]
struct PyL33TMovie {
    pub name: String,
    seeders: Option<u32>,
    leechers: Option<u32>,
    magnet: Option<String>,
}

#[pyfunction]
pub(crate) fn search_leetx(py: Python, term: String) -> Result<Bound<'_, PyAny>, PyErr> {
    pyo3_async_runtimes::tokio::future_into_py(py, async move {
        torrent_search::search_l337x(term)
        .await
        .map(|list| {
                list.into_iter()
                .map(|movie| PyL33TMovie {
                    name: movie.name,
                    leechers: movie.leeches.ok(),
                    seeders: movie.seeders.ok(),
                    magnet: movie.magnet.ok()
                })
                .collect::<Vec<PyL33TMovie>>()
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
                .map(|movie| PyMovie {
                    hash: movie.hash.clone(),
                    seeders: movie.seeds,
                    leechers: movie.peers - movie.seeds,
                    name: movie.quality.clone()
                })
                .collect::<Vec<PyMovie>>())
        })
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Error: {e}")))
    })
}

#[pymodule]
fn attractive(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(search_yts, m)?)?;
    m.add_function(wrap_pyfunction!(search_leetx, m)?)?;
    m.add_class::<PyMovie>()?;
    m.add_class::<PyL33TMovie>()?;
    Ok(())
}
