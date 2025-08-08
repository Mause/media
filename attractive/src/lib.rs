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

#[pyfunction]
async fn get_version(term: &str) -> Result<Vec<PyMovie>, PyErr> {
    Ok(yts_api::ListMovies::new()
        .query_term(term)
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
