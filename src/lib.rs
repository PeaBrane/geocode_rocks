use scraper::{Html, Selector};
use regex::Regex;
use polars::prelude::*;
use futures::future::join_all;
use std::error::Error;
use rand::Rng;
use tokio::time::{sleep, Duration};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use pyo3::prelude::*;
use tokio_util::sync::CancellationToken;
use ctrlc;

async fn get_votes(url: &str) -> Result<u32, Box<dyn std::error::Error>> {
    let html = reqwest::get(url).await?.text().await?;
    let document = Html::parse_document(&html);
    let pattern = Regex::new(r"from\s+(\d+)\s+votes?").unwrap();
    
    let body_selector = Selector::parse("body").unwrap();
    let votes = document
        .select(&body_selector)
        .next()
        .and_then(|body| body.text().find(|text| pattern.is_match(text)))
        .and_then(|text| pattern.captures(text))
        .and_then(|caps| caps.get(1))
        .and_then(|m| m.as_str().parse::<u32>().ok())
        .ok_or("Could not find vote count")?;

    Ok(votes)
}

async fn get_votes_with_retry(url: &str) -> Result<u32, Box<dyn std::error::Error>> {
    let mut attempts = 0;
    let max_attempts = 10;
    let mut rng = rand::thread_rng();
    let base_wait = rng.gen_range(4.0..=6.0);  // Random initial wait time

    while attempts < max_attempts {
        match get_votes(url).await {
            Ok(votes) => return Ok(votes),
            Err(e) => {
                attempts += 1;
                if attempts == max_attempts {
                    return Err(e);
                }
                
                let wait_time = base_wait * 2_f32.powi(attempts - 1);
                let sleep_duration = Duration::from_secs_f32(wait_time);
                
                sleep(sleep_duration).await;
            }
        }
    }
    unreachable!()
}

pub async fn fetch_votes(urls: Vec<String>) -> Vec<Result<u32, Box<dyn Error>>> {
    let total_urls = urls.len();
    let processed = Arc::new(AtomicUsize::new(0));
    let processed_clone = processed.clone();

    // Spawn progress monitoring task
    let progress_task = tokio::spawn(async move {
        loop {
            let current = processed_clone.load(Ordering::Relaxed);
            println!("Progress: {}/{} URLs processed", current, total_urls);
            if current >= total_urls {
                break;
            }
            sleep(Duration::from_secs(2)).await;
        }
    });

    // Run concurrent requests with retry logic
    let futures: Vec<_> = urls
        .iter()
        .map(|url| {
            let processed = processed.clone();
            async move {
                let result = get_votes_with_retry(url).await;
                processed.fetch_add(1, Ordering::Relaxed);
                result
            }
        })
        .collect();

    let results = join_all(futures).await;
    
    // Wait for progress task to finish
    progress_task.await.expect("Progress monitoring task failed");

    results
}

#[pyfunction]
pub fn fetch_votes_py(urls: Vec<String>) -> PyResult<Vec<PyObject>> {
    let rt = tokio::runtime::Runtime::new().unwrap();
    let cancel_token = CancellationToken::new();
    let token_clone = cancel_token.clone();
    
    ctrlc::set_handler(move || {
        token_clone.cancel();
    }).expect("Error setting Ctrl-C handler");
    
    let results = rt.block_on(async {
        tokio::select! {
            r = fetch_votes(urls) => Ok(r),
            _ = cancel_token.cancelled() => {
                Err(pyo3::exceptions::PyKeyboardInterrupt::new_err("Operation cancelled"))
            }
        }
    })?;
    
    results.into_iter().map(|r| {
        match r {
            Ok(votes) => Ok(Python::with_gil(|py| votes.into_py(py))),
            Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(format!("Error: {}", e))),
        }
    }).collect()
}

#[pymodule]
fn rusty_scrapper(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fetch_votes_py, m)?)?;  // Note: using fetch_votes_py here
    Ok(())
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let csv_path = "/Users/peabrane/Documents/codes/geocode_rocks/data/arizona_boulders.csv";
    let num_rows: Option<u32> = None;  // None for all rows, Some(100) for limit

    // Read URLs using Polars
    let df = LazyCsvReader::new(csv_path)
        .has_header(true)
        .finish()?;
    
    // Apply limit only if num_rows is Some
    let df = if let Some(limit) = num_rows {
        df.limit(limit as u32)
    } else {
        df
    }.collect()?;
    
    let urls: Vec<String> = df
        .column("URL")?
        .utf8()?
        .into_iter()
        .flatten()
        .map(String::from)
        .collect();

    let results = fetch_votes(urls.clone()).await;

    // Create results dataframe with -1 for errors
    let votes: Vec<i32> = results
        .into_iter()
        .map(|r| r.ok().map(|v| v as i32).unwrap_or(-1))
        .collect();

    // Create new dataframe with results
    let results_df = DataFrame::new(vec![
        Series::new("URL", &urls),
        Series::new("Votes", &votes),
    ])?;

    // Filter for failed requests and print
    let mask = results_df.column("Votes")?.equal(-1)?;
    let failed_df = results_df.filter(&mask)?;
    
    if failed_df.height() > 0 {
        println!("Failed requests ({} rows):", failed_df.height());
        println!("{}", failed_df);
    } else {
        println!("All requests succeeded!");
    }
    
    Ok(())
}