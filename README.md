## Usage

### Exporting Data from Mountain Project
1. Log in to your Mountain Project account
2. Navigate to the area you want to export (e.g., a specific climbing area or region)
3. Look for the "Export to CSV" option (usually found in the route/problem listing pages)
4. Download the CSV file and place it in the `data` directory of this project

### Processing and Visualization
1. Run the script using the command mentioned above: `make run ARGS="your_exported_file.csv"`
2. Find the processed file (with `_processed.csv` suffix) in the same `data` directory
3. To visualize on Google Maps:
   - Go to [Google My Maps](https://www.google.com/maps/d/)
   - Create a new map
   - Click "Import" and upload your processed CSV file
   - When prompted, select the columns for location data (use the "Latitude" and "Longitude" columns)
   - Configure your map appearance as desired - each pin will now represent a boulder/crag with all routes listed in the description
   - The processed CSV includes a `votes_most_log` column containing the logarithmic vote count of the most popular route at each location, which you can use to create a color-coded map based on popularity

The processed CSV is structured specifically for easy integration with mapping tools, grouping routes by location and including relevant details like grades, star ratings, and vote counts.

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
make run filename="arizona_boulders.csv"
```

This will process the input CSV file (in this example, `data/arizona_boulders.csv`) and generate a processed version with the suffix `_processed.csv` in the same directory (e.g., `data/arizona_boulders_processed.csv`). The script groups climbing problems by their GPS coordinates and includes vote counts from Mountain Project.

## Implementation Details

The core functionality is implemented in Rust for high performance web scraping, which retrieves vote counts for each climbing route from Mountain Project. While the Rust implementation is extremely fast, the script intentionally uses exponential backoff between requests to prevent rate limiting from Mountain Project's servers. This rate limiting is actually the main performance bottleneck, not the processing itself - a deliberate design choice to be respectful of Mountain Project's infrastructure.