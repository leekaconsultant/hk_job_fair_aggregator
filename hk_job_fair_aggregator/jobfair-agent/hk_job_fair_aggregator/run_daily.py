#!/usr/bin/env python3
"""
Main script for running the HK Job Fair Aggregator.
Schedules and executes scrapers for job fair information.
"""

import os
import sys
import time
import argparse
import schedule
from datetime import datetime
import pytz

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logging import setup_logger
from scrapers.labour_dept import LabourDeptScraper
from scrapers.jobsdb import JobsDBScraper
from scrapers.hktdc import HKTDCScraper

# Set up logger
logger = setup_logger('hk_job_fair_aggregator')

def run_primary_scrapers():
    """Run scrapers for primary sources."""
    logger.info("Running primary scrapers")
    
    # Initialize scrapers
    labour_dept_scraper = LabourDeptScraper()
    jobsdb_scraper = JobsDBScraper()
    hktdc_scraper = HKTDCScraper()
    
    # Run scrapers
    labour_dept_scraper.run()
    jobsdb_scraper.run()
    hktdc_scraper.run()
    
    logger.info("Primary scrapers completed")

def run_secondary_scrapers():
    """Run scrapers for secondary sources."""
    logger.info("Running secondary scrapers")
    
    # TODO: Add secondary scrapers when implemented
    logger.info("Secondary scrapers completed")

def run_all_scrapers():
    """Run all scrapers."""
    run_primary_scrapers()
    run_secondary_scrapers()

def setup_schedule():
    """Set up the schedule for running scrapers."""
    # Run primary scrapers daily at 8:00 AM HKT
    schedule.every().day.at("08:00").do(run_primary_scrapers)
    
    # Run secondary scrapers weekly on Monday at 11:00 AM HKT
    schedule.every().monday.at("11:00").do(run_secondary_scrapers)
    
    logger.info("Scheduler set up")
    logger.info("Primary scrapers will run daily at 08:00 HKT")
    logger.info("Secondary scrapers will run weekly on Monday at 11:00 HKT")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='HK Job Fair Aggregator')
    parser.add_argument('--once', action='store_true', help='Run scrapers once and exit')
    parser.add_argument('--primary-only', action='store_true', help='Only run primary scrapers')
    parser.add_argument('--secondary-only', action='store_true', help='Only run secondary scrapers')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logger.setLevel('DEBUG')
    
    # Run once if specified
    if args.once:
        logger.info("Running scrapers once")
        
        if args.primary_only:
            run_primary_scrapers()
        elif args.secondary_only:
            run_secondary_scrapers()
        else:
            run_all_scrapers()
        
        logger.info("Scrapers completed")
        return
    
    # Set up schedule
    setup_schedule()
    
    # Run immediately if specified
    if args.primary_only:
        run_primary_scrapers()
    elif args.secondary_only:
        run_secondary_scrapers()
    else:
        run_all_scrapers()
    
    # Run the scheduler
    logger.info("Starting scheduler")
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, exiting")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)
