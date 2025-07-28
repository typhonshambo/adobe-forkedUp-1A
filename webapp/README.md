# PDF Analysis Web Interface

A web application for interactive PDF document analysis with semantic search capabilities.

## Features

- Responsive web interface
- File upload and analysis
- Real-time results display
- Integration with document analysis backend

## Components

- HTML5 interface with modern styling
- JavaScript for user interaction
- Flask backend API integration
- CSS3 responsive design

## Setup

1. Install dependencies:
   ```bash
   pip install flask flask-cors
   ```

2. Start the server:
   ```bash
   cd webapp
   python app.py
   ```

3. Access the interface at `http://localhost:5000`

## API Endpoints

- `POST /api/analyze` - Process PDF content analysis
- `GET /api/collections` - List available document collections
- `GET /api/health` - Server status check
