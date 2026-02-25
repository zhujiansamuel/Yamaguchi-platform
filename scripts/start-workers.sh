#!/bin/bash

# Script to start all Celery workers in separate terminal sessions
# This is a helper script for development

echo "🔧 Starting Celery Workers..."
echo ""
echo "Note: This will open new terminal windows/tabs for each worker."
echo "Press Ctrl+C in this window won't stop the workers."
echo ""

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "🍎 Detected macOS"

    # Start Acquisition Worker
    osascript -e 'tell app "Terminal" to do script "cd '$(pwd)' && celery -A apps.data_acquisition.celery worker -Q acquisition_queue -n acquisition_worker@%h --loglevel=info"'

    # Start Aggregation Worker
    osascript -e 'tell app "Terminal" to do script "cd '$(pwd)' && celery -A apps.data_aggregation.celery worker -Q aggregation_queue -n aggregation_worker@%h --loglevel=info"'

    # Start Beat (optional)
    # osascript -e 'tell app "Terminal" to do script "cd '$(pwd)' && celery -A config beat --loglevel=info"'

    echo "✅ Celery workers started in new Terminal windows"

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "🐧 Detected Linux"

    # Try different terminal emulators
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash -c "celery -A apps.data_acquisition.celery worker -Q acquisition_queue -n acquisition_worker@%h --loglevel=info; exec bash"
        gnome-terminal -- bash -c "celery -A apps.data_aggregation.celery worker -Q aggregation_queue -n aggregation_worker@%h --loglevel=info; exec bash"
    elif command -v xterm &> /dev/null; then
        xterm -e "celery -A apps.data_acquisition.celery worker -Q acquisition_queue -n acquisition_worker@%h --loglevel=info" &
        xterm -e "celery -A apps.data_aggregation.celery worker -Q aggregation_queue -n aggregation_worker@%h --loglevel=info" &
    else
        echo "❌ No suitable terminal emulator found"
        echo "Please run workers manually:"
        echo "  Terminal 1: celery -A apps.data_acquisition.celery worker -Q acquisition_queue -n acquisition_worker@%h --loglevel=info"
        echo "  Terminal 2: celery -A apps.data_aggregation.celery worker -Q aggregation_queue -n aggregation_worker@%h --loglevel=info"
        exit 1
    fi

    echo "✅ Celery workers started in new terminal windows"

else
    echo "❌ Unsupported OS: $OSTYPE"
    echo "Please run workers manually"
    exit 1
fi

echo ""
echo "📊 Monitor workers:"
echo "  - Check worker status: celery -A apps.data_acquisition.celery inspect active"
echo "  - Check worker status: celery -A apps.data_aggregation.celery inspect active"
