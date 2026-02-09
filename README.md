# Placement Portal

A web application for managing campus placements, built with Flask (Python) for the backend.

## Features
- User authentication (Admin, Company, Student)
- Company and student registration
- Placement drive/job posting management
- Application tracking and approval workflows

## Project Structure
```
Placement Portal/
├── app.py                # Main Flask app entry point
├── requirements.txt      # Python dependencies
├── backend/
│   ├── __init__.py       # App factory
│   ├── controllers.py    # All Flask routes (as Blueprint)
│   ├── models.py         # SQLAlchemy models
├── instance/
│   └── PLACEMENT_PORTAL.sqlite3  # SQLite database (auto-created)
├── static/
│   └── resumes/          # Uploaded resumes
├── templates/            # Jinja2 HTML templates
│   └── ...
```

## Prerequisites
- Python 3.8+
- pip (Python package manager)
- (Recommended) [virtualenv](https://virtualenv.pypa.io/) or [conda](https://docs.conda.io/)

## Backend Setup & Running
1. **Clone the repository** (if not already):
   ```sh
   git clone <repo-url>
   cd "Placement Portal"
   ```
2. **Create and activate a virtual environment** (recommended):
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   # or with conda:
   # conda create -n placement-portal python=3.10
   # conda activate placement-portal
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Run the backend server:**
   ```sh
   python app.py
   ```
   The server will start on [http://localhost:5001](http://localhost:5001)

5. **Default Admin Login:**
   - Email: `admin@iitm.ac.in`
   - Password: `admin123`

## Frontend
This project uses Flask/Jinja2 templates for the frontend. All HTML files are in the `templates/` folder. Static files (CSS, JS, resumes) are in `static/`.
- Access the app in your browser at [http://localhost:5001](http://localhost:5001)

## Database
- The app uses SQLite by default (`instance/PLACEMENT_PORTAL.sqlite3`).
- To use another database, set the `DATABASE_URL` environment variable in a `.env` file.

## Environment Variables
Create a `.env` file in the root directory (optional):
```
DATABASE_URL=sqlite:///PLACEMENT_PORTAL.sqlite3
SECRET_KEY=placement_secret_key
```

## File Uploads
- Student resumes are uploaded to `static/resumes/`.

## Troubleshooting
- If you get `ModuleNotFoundError`, ensure your virtual environment is activated and dependencies are installed.
- For database issues, delete the `instance/PLACEMENT_PORTAL.sqlite3` file to reset (will remove all data).

## Customization
- To add more user roles or features, edit `backend/models.py` and `backend/controllers.py`.
- To change the UI, edit files in `templates/` and `static/`.

## License
MIT (or specify your license)
