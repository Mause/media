//#![feature(experimental_async)]
// rustimport:pyo3

//: [package]
//: version = "1.2.3"
//:

use pyo3::prelude::*;

#[pyclass]
struct PyMovie {
    id: u32,
    title: String,
    year: u32,
    rating: f32,
}

#[pyclass]
struct PyL33TMovie {
    name: String,
}

#[pyfunction]
async fn search_leetx(term: String) -> Result<Vec<PyL33TMovie>, PyErr> {
    Ok(torrent_search::search_l337x(term)
        .await
        .map(|list| {
            list
                .into_iter()
                .map(|movie| PyL33TMovie {
                    name: movie.name,
                })
                .collect::<Vec<PyL33TMovie>>()
        })
        .unwrap())
}

#[pyfunction]
async fn search_yts(term: String) -> Result<Vec<PyMovie>, PyErr> {
    Ok(yts_api::ListMovies::new()
        .query_term(&term)
        .execute()
        .await
        .map(|list| {
            list.movies
                .into_iter()
                .map(|movie| PyMovie {
                    id: movie.id,
                    title: movie.title,
                    year: movie.year,
                    rating: movie.rating,
                })
                .collect::<Vec<PyMovie>>()
        })
        .unwrap())
}
