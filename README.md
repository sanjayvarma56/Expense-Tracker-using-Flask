# Personal Expense Tracker

## Included features
- Add expenses (CREATE)
- Display expenses (READ)
- Edit expenses (UPDATE)
- Delete expenses (DELETE)
- Filter by start date, end date and category
- Dynamic total for filtered expenses
- Category bar chart
- Daily spending line chart
- Category distribution pie chart with hover percentages
- Export currently filtered expenses to CSV

## Project structure
```text
expense_tracker_final/
├── app.py
└── templates/
    ├── index.html
    └── edit.html
```

## Install dependencies
```bash
python3 -m pip install Flask Flask-SQLAlchemy
```

## Run
```bash
python3 app.py
```

Open http://127.0.0.1:4848

The SQLite database is created automatically by Flask-SQLAlchemy.
The database URI uses Flask-SQLAlchemy's default instance folder location.
Back up your existing database before replacing an older project version.

For deployment, set a secure SECRET_KEY in the environment instead of using
the development fallback in app.py.
