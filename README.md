# Blog2Audio

Blog2Audio is a web application that converts blog posts into audio format. It allows users to input a URL of a blog post, and then it fetches the text, converts it into speech using OpenAI's Text-to-Speech service, and provides an audio version of the blog post for the user to listen to.

## Features

- Input field for users to submit the URL of a blog post
- Enhanced content extraction with multiple methods to ensure quality results
- Text processing for better speech output
- Text-to-Speech conversion using OpenAI's API with multiple voice options
- An enhanced audio player with playback speed control and volume settings
- Background processing for handling long articles
- Progress tracking with real-time updates
- Caching system to reduce duplicate processing
- User session tracking
- Responsive design that works on mobile devices
- Dark mode support
- API endpoints for programmatic access
- Download functionality to save audio files

## Technology Stack

- **Backend**: Flask, Python 3.10+
- **Database**: SQLAlchemy with SQLite (development) / PostgreSQL (production)
- **Content Extraction**: Beautiful Soup, Trafilatura, Newspaper3k, Readability
- **Text Processing**: NLTK, langdetect
- **Audio**: OpenAI API, pydub
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Deployment**: Gunicorn, Heroku/Render/PythonAnywhere compatible

## Setup and Installation

### Prerequisites

- Python 3.10 or higher
- OpenAI API key
- pip (Python package manager)
- Virtual environment (recommended)

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/blog2audio.git
   cd blog2audio
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on the example:
   ```bash
   cp .env.example .env
   ```

5. Edit the `.env` file and add your OpenAI API key and other configuration.

6. Initialize the database:
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

7. Run the development server:
   ```bash
   python run.py
   ```

8. Open your browser and navigate to `http://127.0.0.1:5000`.

### Production Deployment

#### Heroku Deployment

1. Create a Heroku account and install the Heroku CLI.

2. Login to Heroku:
   ```bash
   heroku login
   ```

3. Create a new Heroku app:
   ```bash
   heroku create your-app-name
   ```

4. Add a PostgreSQL database:
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

5. Set environment variables:
   ```bash
   heroku config:set FLASK_ENV=production
   heroku config:set FLASK_CONFIG=production
   heroku config:set SECRET_KEY=your-secure-secret-key
   heroku config:set OPENAI_API_KEY=your-openai-api-key
   heroku config:set LOG_TO_STDOUT=true
   ```

6. Deploy the application:
   ```bash
   git push heroku main
   ```

7. Initialize the database:
   ```bash
   heroku run flask db upgrade
   ```

#### Render Deployment

1. Create a Render account at [render.com](https://render.com/).

2. Connect your GitHub repository.

3. Create a new Web Service with the following settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn wsgi:application`

4. Add environment variables in the Render dashboard:
   - `FLASK_ENV`: production
   - `FLASK_CONFIG`: production
   - `SECRET_KEY`: your-secure-secret-key
   - `OPENAI_API_KEY`: your-openai-api-key
   - `DATABASE_URL`: your-postgres-connection-string
   - `LOG_TO_STDOUT`: true

5. Deploy the service.

## Project Structure

```
blog2audio/
├── app/
│   ├── __init__.py             # Application factory
│   ├── config.py               # Configuration settings
│   ├── routes/                 # Route handlers
│   │   ├── __init__.py
│   │   ├── main.py             # Main routes
│   │   └── api.py              # API routes
│   ├── services/               # Business logic services
│   │   ├── __init__.py
│   │   ├── content_extractor.py # Enhanced content extraction
│   │   ├── text_processor.py    # Text processing for better speech
│   │   └── audio_converter.py   # TTS conversion
│   ├── models/                 # Database models
│   │   ├── __init__.py
│   │   └── audio_content.py
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       └── helpers.py
├── static/                     # Static assets
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── audio/                  # Generated audio files
├── templates/                  # HTML templates
│   ├── base.html
│   ├── index.html
│   └── result.html
├── migrations/                 # Database migrations
├── instance/                   # Instance-specific configurations
├── .env.example                # Example environment variables
├── .gitignore                  # Git ignore file
├── requirements.txt            # Project dependencies
├── run.py                      # Development server entry point
└── wsgi.py                     # Production WSGI entry point
```

## API Usage

### Converting a URL

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/blog-post", "voice": "onyx"}' \
  https://your-app-domain.com/api/convert
```

### Checking Status

```bash
curl https://your-app-domain.com/api/status/123
```

### Getting Available Voices

```bash
curl https://your-app-domain.com/api/voices
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [OpenAI](https://openai.com/) for the Text-to-Speech API
- [Flask](https://flask.palletsprojects.com/) web framework
- [Trafilatura](https://trafilatura.readthedocs.io/) for web content extraction
- [NLTK](https://www.nltk.org/) for text processing