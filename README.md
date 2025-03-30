This short python script processes the data exported (in csv format) from Mountain Project, such that all the problems are grouped into boulders/crags (based on their GPS coordinate similarities).

This is for the purpose of uploading the processed data into mapping applications such as Google Maps, such that each displayed pin corresponds to a boulder/crag, with the routes/grades/stars listed as description for easier organization.

## Prerequisites

- A working Rust installation ([Install Rust](https://www.rust-lang.org/tools/install))
- Python environment (3.7 or higher recommended)

## Building and Running

This project uses a Makefile for easy building and execution. Make sure you have `make` installed on your system.

### Build
To install dependencies and build the project:
```bash
make build
```

The build command performs the following steps:
1. Installs Python dependencies including `maturin` (the tool that builds and bridges Rust and Python)
2. Uses `maturin` to compile the Rust code and generate Python bindings
3. Builds the project in release mode for optimal performance

### Run
To run the script:
```bash
make run filename=arizona_boulders.csv
```

This will process the input CSV file (in this example, `data/arizona_boulders.csv`) and generate a processed version with the suffix `_processed.csv` in the same directory (e.g., `data/arizona_boulders_processed.csv`). The script groups climbing problems by their GPS coordinates and includes vote counts from Mountain Project.

## Implementation Details

The core functionality is implemented in Rust for high performance web scraping, which retrieves vote counts for each climbing route from Mountain Project. While the Rust implementation is extremely fast, the script intentionally uses exponential backoff between requests to prevent rate limiting from Mountain Project's servers. This rate limiting is actually the main performance bottleneck, not the processing itself - a deliberate design choice to be respectful of Mountain Project's infrastructure.