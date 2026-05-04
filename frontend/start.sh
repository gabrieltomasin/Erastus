#!/bin/sh
# Start Next.js on port 3001 in background, then nginx on port 3000 in foreground
PORT=3001 node node_modules/.bin/next start &
nginx -g 'daemon off;'
