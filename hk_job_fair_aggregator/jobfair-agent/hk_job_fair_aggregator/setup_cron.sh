#!/bin/bash
# Setup cron job for HK Job Fair Aggregator

# Get the absolute path to the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Make run_daily.py executable
chmod +x "$SCRIPT_DIR/run_daily.py"

# Create a temporary file for the crontab
TEMP_CRON=$(mktemp)

# Export current crontab to the temporary file
crontab -l > "$TEMP_CRON" 2>/dev/null || echo "# New crontab" > "$TEMP_CRON"

# Check if the cron job already exists
if grep -q "hk_job_fair_aggregator/run_daily.py" "$TEMP_CRON"; then
    echo "Cron job already exists. Skipping..."
else
    # Add the cron job to run daily at 7:00 AM HKT (UTC+8)
    echo "# HK Job Fair Aggregator - Run daily at 7:00 AM HKT" >> "$TEMP_CRON"
    echo "0 7 * * * cd $SCRIPT_DIR && python3 $SCRIPT_DIR/run_daily.py >> $SCRIPT_DIR/logs/cron.log 2>&1" >> "$TEMP_CRON"
    
    # Install the new crontab
    crontab "$TEMP_CRON"
    echo "Cron job installed successfully."
fi

# Clean up
rm "$TEMP_CRON"

echo "Setup complete."
echo "The HK Job Fair Aggregator will run daily at 7:00 AM HKT."
echo "Logs will be saved to $SCRIPT_DIR/logs/cron.log"
