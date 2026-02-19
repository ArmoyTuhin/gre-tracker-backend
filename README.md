# GRE Error Tracker - Backend API

FastAPI backend for the GRE Error Tracker application with spaced repetition system (SRS) using the SM-2 algorithm.

## Features

- 📝 **Mistake Management**: Create, read, update, and delete GRE mistakes
- 🔄 **Spaced Repetition**: Automatic review scheduling using SM-2 algorithm
- 📊 **Review System**: Get today's reviews separated by Quant and Verbal
- 🎯 **Mastery Tracking**: Items marked as mastered after 5 successful reviews
- 📐 **Export Functionality**: Export mistakes to Excel and PDF formats
- 📚 **Vocabulary Management**: Track vocabulary words with filters
- 🎴 **Exam Sessions**: Create and track exam sessions with statistics

## Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Production database (SQLite for local dev)
- **SM-2 Algorithm** - Spaced repetition scheduling
- **OpenPyXL** - Excel export
- **ReportLab** - PDF export

## Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL (optional, uses SQLite by default)

### Setup

1. **Clone the repository**:
   ```bash
   git clone <your-backend-repo-url>
   cd gre-tracker-backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your DATABASE_URL if using PostgreSQL
   ```

5. **Run the server**:
   ```bash
   uvicorn main:app --reload
   ```

   Backend will be available at `http://localhost:8000`
   API docs at `http://localhost:8000/docs`

## Deployment to Railway

### Prerequisites

- Railway account at [railway.app](https://railway.app)
- GitHub repository with this code

### Steps

1. **Create a new Railway project**:
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your backend repository

2. **Add PostgreSQL service**:
   - In your Railway project, click "+ New"
   - Select "PostgreSQL"
   - Railway will automatically provide `DATABASE_URL` environment variable

3. **Configure the backend service**:
   - Railway should auto-detect the `Procfile`
   - If not, add a new service and select "Empty Service"
   - Set **Root Directory** to `.` (current directory)
   - Railway will automatically detect Python and install dependencies

4. **Set environment variables**:
   - `DATABASE_URL` - Automatically set from PostgreSQL service
   - `PORT` - Automatically set by Railway
   - `ALLOWED_ORIGINS` - Add your frontend URL (e.g., `https://your-app.vercel.app`)

5. **Deploy**:
   - Railway will automatically deploy on push to main branch
   - Or manually trigger deployment from Railway dashboard

6. **Get your backend URL**:
   - After deployment, Railway will provide a URL like `https://your-app.railway.app`
   - Use this URL in your frontend's `NEXT_PUBLIC_API_URL` environment variable

## Environment Variables

### Required (Auto-set by Railway)
- `DATABASE_URL` - PostgreSQL connection string (from PostgreSQL service)
- `PORT` - Server port (set automatically by Railway)

### Optional
- `ALLOWED_ORIGINS` - Comma-separated list of allowed CORS origins
  - Example: `https://your-app.vercel.app,http://localhost:3000`

## API Endpoints

### Mistake Management
- `GET /mistakes/` - Get all mistakes (with optional filters)
- `POST /mistakes/` - Create a new mistake
- `GET /mistakes/{id}` - Get a specific mistake
- `PUT /mistakes/{id}` - Update a mistake
- `DELETE /mistakes/{id}` - Delete a mistake
- `GET /mistakes/export/excel` - Export mistakes to Excel
- `GET /mistakes/export/pdf` - Export mistakes to PDF

### Review System
- `GET /review/today` - Get today's reviews (separated by Quant/Verbal)
- `POST /review/{id}/submit` - Submit a review with quality score (1-5)

### Vocabulary
- `GET /vocabulary` - Get vocabulary list (with optional filters)
- `POST /vocabulary` - Create vocabulary entry
- `GET /vocabulary/{id}` - Get specific vocabulary
- `PUT /vocabulary/{id}` - Update vocabulary
- `DELETE /vocabulary/{id}` - Delete vocabulary
- `GET /vocabulary/export/excel` - Export vocabulary to Excel
- `GET /vocabulary/export/pdf` - Export vocabulary to PDF

### Exam Sessions
- `POST /exam/create` - Create exam session
- `GET /exam/{id}` - Get exam session
- `POST /exam/{id}/submit-answer` - Submit answer
- `POST /exam/{id}/complete` - Complete exam
- `GET /exam/history` - Get exam history
- `GET /exam/statistics` - Get exam statistics

## Database

The application uses:
- **PostgreSQL** in production (Railway)
- **SQLite** for local development (if `DATABASE_URL` is not set)

Tables are automatically created on first run using SQLAlchemy's `create_all()`.

## CORS Configuration

Update `ALLOWED_ORIGINS` in `app/main.py` or via environment variable to allow your frontend domain.

## License

MIT License

