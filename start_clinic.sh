#!/bin/bash

# Move to project folder
cd /Users/utkarshaggarwal/Desktop/aggarwal_clinic

# Activate virtual environment
source venv/bin/activate

# Start Flask in background
python app.py &

# Wait for server to start
sleep 2

# Open browser automatically
open http://localhost:5000
