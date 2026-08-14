#!/bin/bash
# Start Node.js Express server on port 3000 in the background for health checks
npm start &

# Start Python Discord Bot
python -m bot.main
