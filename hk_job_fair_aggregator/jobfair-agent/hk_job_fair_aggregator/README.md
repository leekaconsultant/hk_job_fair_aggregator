# Hong Kong Job Fair Aggregator

A Python-based system for automated collection of job fair and recruitment event information in Hong Kong. This system scrapes data from various sources, normalizes it, and stores it in a structured format for easy access and integration with Google Calendar.

## Features

- Automated web scraping of job fair information from major Hong Kong sources
- Support for Traditional Chinese (ZH-HK) content
- Daily scheduling for primary sources and weekly for secondary sources
- Data normalization and deduplication
- Structured JSON storage
- Comprehensive logging and error handling

## Directory Structure

```
hk_job_fair_aggregator/
├── scrapers/              # Source-specific scraper modules
│   ├── __init__.py
│   ├── base.py            # Base scraper class
│   ├── labour_dept.py     # Hong Kong Labour Department scraper
│   ├── jobsdb.py          # JobsDB Hong Kong scraper
│   └── hktdc.py           # Hong Kong Trade Development Council scraper
├── utils/                 # Utility modules
│   ├── __init__.py
│   ├── logging.py         # Logging configuration
│   └── normalizer.py      # Data normalization utilities
├── data/                  # Storage for scraped data
├── logs/                  # Log files
├── run_daily.py           # Main script for daily execution
└── setup_cron.sh          # Script to set up cron job
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/hk_job_fair_aggregator.git
cd hk_job_fair_aggregator
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Manual Execution

To run the scraper manually:

```bash
python run_daily.py
```

Options:
- `--once`: Run the scraper once without scheduling
- `--primary-only`: Only run scrapers for primary sources
- `--secondary-only`: Only run scrapers for secondary sources
- `--verbose`: Enable verbose logging

### Scheduled Execution

To set up automatic daily execution:

```bash
bash setup_cron.sh
```

This will add a cron job that runs the primary scrapers daily and the secondary scrapers weekly.

## Data Output

Scraped data is stored in JSON files in the `data/` directory with the following naming convention:

```
data/
├── labour_dept_YYYY-MM-DD.json
├── jobsdb_YYYY-MM-DD.json
└── hktdc_YYYY-MM-DD.json
```

Each JSON file contains an array of job fair events with standardized fields according to the database schema.

## Logging

Logs are stored in the `logs/` directory with daily rotation. The log level can be configured in `utils/logging.py`.

## Requirements

- Python 3.8+
- BeautifulSoup4
- Requests
- Selenium (for dynamic content)
- Schedule
- pytz
- python-dateutil

## License

This project is licensed under the MIT License - see the LICENSE file for details.
