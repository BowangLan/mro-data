# MRO Data API and Display Modules

This directory contains scripts for interacting with the MRO data server, with a clean separation between API functionality and display concerns.

## Architecture Overview

The code is organized with **separation of concerns**:

- **`mro_api.py`** - Pure API functionality (server communication, data handling)
- **`mro_display.py`** - Display/UI functionality (progress bars, tables, console output)
- **Scripts** - Combine both modules for command-line tools

## Files Overview

### Core Modules
- **`mro_api.py`** - Clean API wrapper for MRO data server operations
- **`mro_display.py`** - Display handler for UI/console output

### Original Scripts
- **`download_fits.py`** - Original script for downloading FITS files
- **`list_available_days.py`** - Original script for listing available days

### New Scripts (using separated modules)
- **`download_fits_v2.py`** - Updated download script using separated API and Display
- **`list_available_days_v2.py`** - Updated list script using separated API and Display
- **`example_api_usage.py`** - Example demonstrating the separated architecture

## MRODataAPI Class

The `MRODataAPI` class provides **pure API functionality** - no display concerns.

### Basic Usage

```python
from mro_api import MRODataAPI

# Initialize the API wrapper
api = MRODataAPI()

# List all available days (returns raw data)
dates = await api.list_available_days()

# Download data for a specific date (returns statistics)
result = await api.download_date_data('20250704', output_dir='data')
```

### Key Methods

#### `list_available_days()`
Lists all available days for download.

**Returns:**
- List of available dates in YYYYMMDD format
- Raises exceptions on errors (no console output)

#### `get_files_for_date(date)`
Get list of FITS files available for a specific date.

**Parameters:**
- `date` (str): Date in YYYYMMDD format

**Returns:**
- List of FITS file names
- Raises exceptions on errors

#### `download_date_data(date, output_dir="data", force=False, max_concurrent=5)`
Download all FITS files for a specific date.

**Parameters:**
- `date` (str): Date in YYYYMMDD format
- `output_dir` (str): Output directory for downloaded files
- `force` (bool): Force re-download of existing files
- `max_concurrent` (int): Maximum number of concurrent downloads

**Returns:**
- Dictionary with download statistics:
  ```python
  {
      "success": bool,
      "downloaded": int,
      "skipped": int,
      "failed": int,
      "total": int,
      "output_dir": str,
      "error": str  # if error occurred
  }
  ```

## MRODisplay Class

The `MRODisplay` class handles **all display and UI concerns**.

### Basic Usage

```python
from mro_display import MRODisplay
from rich.console import Console

# Initialize display
console = Console()
display = MRODisplay(console)

# Display various UI elements
display.show_dates_table(dates)
display.show_download_summary(result)
display.show_success_message()
```

### Key Methods

#### `show_dates_table(dates)`
Display dates in a formatted Rich table.

#### `show_download_summary(result)`
Display download statistics in a table.

#### `show_success_message(message)`
Display success message.

#### `show_error_message(message)`
Display error message.

#### `show_configuration(config)`
Display configuration information.

## Usage Examples

### 1. API Only (No Display)

```python
import asyncio
from mro_api import MRODataAPI

async def main():
    api = MRODataAPI()
    
    # Get raw data - no display
    dates = await api.list_available_days()
    print(f"Found {len(dates)} dates: {dates[:3]}...")
    
    # Download data - no display
    result = await api.download_date_data('20250704')
    print(f"Download result: {result}")

asyncio.run(main())
```

### 2. Display Only (Using Data from API)

```python
from mro_display import MRODisplay

# Use data from API
dates = ['20250704', '20250705', '20250706']
result = {"downloaded": 10, "skipped": 2, "failed": 0, "total": 12}

# Display the data
display = MRODisplay()
display.show_dates_table(dates)
display.show_download_summary(result)
```

### 3. Combined Usage (As in Scripts)

```python
import asyncio
from mro_api import MRODataAPI
from mro_display import MRODisplay

async def main():
    # Initialize both
    api = MRODataAPI()
    display = MRODisplay()
    
    # Get data
    dates = await api.list_available_days()
    
    # Display data
    display.show_dates_table(dates)
    display.show_dates_summary(dates)

asyncio.run(main())
```

## Command Line Usage

### Using the new v2 scripts:

```bash
# List available days
python scripts/list_available_days_v2.py

# Download data for a specific date
python scripts/download_fits_v2.py 20250704

# Download with custom options
python scripts/download_fits_v2.py 20250704 --output-dir data --force --max-concurrent 10
```

### Using the original scripts:

```bash
# List available days
python scripts/list_available_days.py

# Download data for a specific date
python scripts/download_fits.py 20250704
```

## Benefits of Separation

### **Clean API**
- `MRODataAPI` focuses only on server communication
- No display dependencies
- Easy to test and mock
- Can be used in headless environments

### **Flexible Display**
- `MRODisplay` handles all UI concerns
- Can be easily modified or replaced
- Supports different output formats
- Separated from business logic

### **Better Testing**
- API can be tested without display
- Display can be tested with mock data
- Easier to unit test individual components

### **Reusability**
- API can be used in different contexts (CLI, web, library)
- Display can be adapted for different UIs
- Clear separation of responsibilities

## Dependencies

### API Module (`mro_api.py`)
- `httpx` - For HTTP requests
- `beautifulsoup4` - For HTML parsing

### Display Module (`mro_display.py`)
- `rich` - For console output and progress bars

### Scripts
- Both modules plus standard library

## Migration from Original Scripts

The original scripts mixed API and display concerns. The new architecture:

1. **Extracts API logic** into `MRODataAPI`
2. **Extracts display logic** into `MRODisplay`
3. **Updates scripts** to use both modules
4. **Maintains compatibility** with convenience functions

This provides a cleaner, more maintainable, and more testable codebase. 