# app.py
from flask import Flask, render_template, request, url_for
import csv

app = Flask(__name__, static_folder='static')

def read_csv(file_path):
    with open(file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        headers = csv_reader.fieldnames
        rows = [row for row[4:] in csv_reader]
    return headers, rows

def fetch_all_images():
    headers, rows = read_csv('image_paths.csv')
    return headers, rows

@app.route('/')
def display_images():
    headers, rows = read_csv('image_paths.csv')
    page = request.args.get('page', '1')
    
    if page == 'all':
        # Show all images
        paginated_rows = rows
        per_page = len(rows)
    else:
        # Paginate
        page = int(page)
        per_page = 20
        start = (page - 1) * per_page
        end = start + per_page
        paginated_rows = rows[start:end]

    total = len(rows)
    return render_template('index.html', headers=headers, rows=paginated_rows, page=page, total=total, per_page=per_page)

if __name__ == '__main__':
    app.run(debug=True)
