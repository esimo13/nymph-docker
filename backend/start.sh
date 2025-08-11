#!/bin/bash

# Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port $PORT
