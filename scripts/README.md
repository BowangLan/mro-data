# MRO Data Download Scripts

This directory contains scripts for downloading FITS files from the MRO (Mars Reconnaissance Orbiter) data server.

## Files

- `download_fits.py` - Main script for downloading FITS files from a specific date
- `example_usage.py` - Example of how to use the download functionality programmatically
- `sync_data.py` - Original file containing the HTML response example

## Usage

### Command Line Usage

Download all FITS files for a specific date:

```bash
# Download data for July 4, 2025 (skips existing files)
python scripts/download_fits.py 20250704

# Force re-download of all files (even existing ones)
python scripts/download_fits.py 20250704 --force

# Use custom output directory
python scripts/download_fits.py 20250704 --output-dir my_data
```

This will:
1. Create a directory `data/20250704/` (or your custom directory)
2. Download all FITS files from `http://72.233.250.83/data/ecam/20250704/`
3. Save them to the local directory
4. Skip files that already exist and have the correct size (unless `--force` is used)

### Command Line Options

```bash
python scripts/download_fits.py --help
```

Available options:
- `date`: Date in YYYYMMDD format (required)
- `--output-dir`: Output directory (default: `data`)
- `--base-url`: Base URL for the data server (default: `http://72.233.250.83/data/ecam`)
- `--force`: Force re-download of existing files

### Programmatic Usage

```python
from scripts.download_fits import download_date_data

# Download data for July 4, 2025
success = download_date_data(
    date="20250704",
    base_url="http://72.233.250.83/data/ecam",
    output_dir="data"
)

if success:
    print("All files downloaded successfully!")
else:
    print("Some files failed to download.")
```

### Example Script

Run the example script to see it in action:

```bash
python scripts/example_usage.py
```

## Features

- **Progress tracking**: Shows download progress for each file
- **Smart resume capability**: 
  - Skips files that already exist and have the correct size
  - Automatically re-downloads incomplete files
  - Provides detailed statistics about skipped vs downloaded files
- **Force re-download**: Use `--force` flag to re-download all files
- **Error handling**: Gracefully handles network errors and missing files
- **Rate limiting**: Small delays between downloads to be respectful to the server
- **HTML parsing**: Automatically parses the directory listing to find all FITS files
- **Detailed reporting**: Shows download summary with counts of downloaded, skipped, and failed files

## Dependencies

The script requires the following Python packages:
- `requests` - For HTTP requests
- `beautifulsoup4` - For parsing HTML directory listings

These are already included in the project's `pyproject.toml` file.

## Data Format

The script downloads FITS files with names like:
- `ecam-0001.fits`
- `ecam-0002.fits`
- ...
- `ecam-0123.fits`

Each file is approximately 2MB in size.

## Output Structure

Files are organized by date:
```
data/
├── 20250704/
│   ├── ecam-0001.fits
│   ├── ecam-0002.fits
│   └── ...
└── 20250705/
    ├── ecam-0001.fits
    └── ...
``` 