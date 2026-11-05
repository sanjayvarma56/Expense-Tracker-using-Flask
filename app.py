#Expense Tracker Project
from datetime import date, datetime
from io import StringIO
import csv
import math
import os
from flask import (Flask,render_template,request,redirect,url_for,flash,make_response,
)
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "change-this-development-key"
)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///expenses_data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
CATEGORIES = ["Food", "Transport", "Rent", "Utilities"]
# Database model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
# Create the database tables.
with app.app_context():
    db.create_all()
def parse_expense_form(form):
    """Validate and clean data submitted by the add/edit expense forms."""
    description = (form.get("description") or "").strip()
    amount_text = (form.get("amount") or "").strip()
    date_text = (form.get("date") or "").strip()
    category = (form.get("category") or "").strip()

    if not description or not amount_text or not date_text or not category:
        raise ValueError("Please complete all expense fields.")
    if len(description) > 200:
        raise ValueError("Description must be 200 characters or fewer.")
    if category not in CATEGORIES:
        raise ValueError("Please choose a valid category.")
    try:
        amount = float(amount_text)
    except ValueError:
        raise ValueError("Amount must be a valid number.")
    if not math.isfinite(amount) or amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    try:
        expense_date = datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Please enter a valid date.")

    return description, amount, expense_date, category

def filtered_expenses(args):
    """
    Apply optional start-date, end-date and category filters.
    The same function is used by the dashboard and CSV export.
    """
    query = Expense.query
    start_text = (args.get("start_date") or "").strip()
    end_text = (args.get("end_date") or "").strip()
    category = (args.get("filter_category") or "").strip()

    start_date = None
    end_date = None

    if start_text:
        try:
            start_date = datetime.strptime(start_text, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Please enter a valid start date.")

    if end_text:
        try:
            end_date = datetime.strptime(end_text, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Please enter a valid end date.")

    if start_date and end_date and start_date > end_date:
        raise ValueError("Start date cannot be later than end date.")

    if category and category not in CATEGORIES:
        raise ValueError("Please choose a valid category filter.")

    if start_date:
        query = query.filter(Expense.date >= start_date)

    if end_date:
        query = query.filter(Expense.date <= end_date)

    if category:
        query = query.filter(Expense.category == category)

    return query.order_by(Expense.date.desc(), Expense.id.desc()).all()
@app.route("/")
def index():
    try:
        expenses = filtered_expenses(request.args)
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("index"))

    total_amount = sum(expense.amount for expense in expenses)

    # Prepare category totals for the bar and pie charts.
    category_totals = {}
    for expense in expenses:
        category_totals[expense.category] = (
            category_totals.get(expense.category, 0) + expense.amount
        )

    category_labels = list(category_totals.keys())
    category_values = [
        round(value, 2) for value in category_totals.values()
    ]

    # Prepare daily totals for the line chart.
    daily_totals = {}
    for expense in expenses:
        day_label = expense.date.isoformat()
        daily_totals[day_label] = (
            daily_totals.get(day_label, 0) + expense.amount
        )

    daily_labels = sorted(daily_totals.keys())
    daily_values = [
        round(daily_totals[label], 2) for label in daily_labels
    ]
    return render_template(
        "index.html",
        expenses=expenses,
        total_amount=total_amount,
        categories=CATEGORIES,
        category_labels=category_labels,
        category_values=category_values,
        daily_labels=daily_labels,
        daily_values=daily_values,
        today=date.today().isoformat(),
    )

# CREATE: Add a new expense.
@app.route("/add", methods=["POST"])
def add_expense():
    try:
        description, amount, expense_date, category = parse_expense_form(
            request.form
        )
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("index"))

    expense = Expense(
        description=description,
        amount=amount,
        date=expense_date,
        category=category,
    )

    db.session.add(expense)
    db.session.commit()

    flash("Expense added successfully.", "success")
    return redirect(url_for("index"))


# UPDATE: Display the edit form and save changes.
@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    expense = db.get_or_404(Expense, expense_id)

    if request.method == "POST":
        try:
            description, amount, expense_date, category = parse_expense_form(
                request.form
            )
        except ValueError as error:
            flash(str(error), "error")
            return redirect(
                url_for("edit_expense", expense_id=expense.id)
            )

        expense.description = description
        expense.amount = amount
        expense.date = expense_date
        expense.category = category

        db.session.commit()

        flash("Expense updated successfully.", "success")
        return redirect(url_for("index"))

    return render_template(
        "edit.html",
        expense=expense,
        categories=CATEGORIES,
    )


# DELETE: Delete an expense using a POST request.
@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    expense = db.get_or_404(Expense, expense_id)

    db.session.delete(expense)
    db.session.commit()

    flash("Expense deleted successfully.", "success")
    return redirect(url_for("index"))


# EXPORT: Download only the records matching the active filters.
@app.route("/export-csv")
def export_csv():
    try:
        expenses = filtered_expenses(request.args)
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("index"))

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["ID", "Date", "Description", "Category", "Amount"])

    for expense in expenses:
        writer.writerow(
            [
                expense.id,
                expense.date.isoformat(),
                expense.description,
                expense.category,
                f"{expense.amount:.2f}",
            ]
        )

    # UTF-8 BOM improves compatibility when opening the CSV in Excel.
    csv_content = "\ufeff" + output.getvalue()

    response = make_response(csv_content)
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = (
        "attachment; filename=filtered_expenses.csv"
    )
    return response


if __name__ == "__main__":
    app.run(debug=True, port=4848)