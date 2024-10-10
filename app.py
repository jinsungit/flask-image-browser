# app.py
from flask import Flask, render_template, request, url_for, session, redirect
import csv
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='static')
app.secret_key = 'your_secret_key_here'  # Set a secret key for session management
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'temp_files')  # Make sure this directory exists

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/load_csv', methods=['POST'])
def load_csv():
    input_method = request.form['input_method']

    if input_method == 'upload':
        if 'csv_file' not in request.files:
            return "No file part", 400
        file = request.files['csv_file']
        if file.filename == '':
            return "No selected file", 400
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
    elif input_method == 'path':
        file_path = request.form['csv_path']
        if not os.path.exists(file_path):
            return f"CSV file not found: {file_path}", 400
        if not os.path.isfile(file_path):
            return f"Path exists but is not a file: {file_path}", 400
        if not os.access(file_path, os.R_OK):
            return f"File exists but is not readable: {file_path}", 400
    else:
        return "Invalid input method", 400

    try:
        headers, rows = read_csv(file_path)
        
        # Save data to a temporary JSON file
        data_filename = f"{os.path.basename(file_path)}_data.json"
        data_path = os.path.join(app.config['UPLOAD_FOLDER'], data_filename)
        with open(data_path, 'w') as f:
            json.dump({'headers': headers, 'rows': rows}, f)
        
        # Store only the filename in the session
        session['csv_data_file'] = data_filename
        
        return redirect(url_for('display_images'))
    except Exception as e:
        return f"Error reading CSV file: {str(e)}", 400

def is_valid_image_path(path):
    if not os.path.exists(path):
        return False
    _, ext = os.path.splitext(path)
    return ext.lower() in ['.jpg', '.jpeg', '.png', '.gif']

def read_csv(file_path):
    with open(file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        headers = [h for h in csv_reader.fieldnames]
        rows = []
        for row in csv_reader:
            processed_row = {}
            for h in headers:
                value = row[h]
                if is_valid_image_path(value):
                    processed_row[h] = {'type': 'image', 'path': value}
                else:
                    processed_row[h] = {'type': 'text', 'value': value}
            rows.append(processed_row)
    return headers, rows

@app.route('/images')
def display_images():
    if 'csv_data_file' not in session:
        return redirect(url_for('landing'))

    data_path = os.path.join(app.config['UPLOAD_FOLDER'], session['csv_data_file'])
    if not os.path.exists(data_path):
        return "Data file not found. Please upload the CSV file again.", 400

    with open(data_path, 'r') as f:
        data = json.load(f)

    headers = data['headers']
    rows = data['rows']
    page = request.args.get('page', '1')
    
    if page == 'all':
        paginated_rows = rows
        per_page = len(rows)
    else:
        page = int(page)
        per_page = 20
        start = (page - 1) * per_page
        end = start + per_page
        paginated_rows = rows[start:end]

    total = len(rows)
    return render_template('gallery.html', headers=headers, rows=paginated_rows, page=page, total=total, per_page=per_page)

if __name__ == '__main__':
    app.run(debug=True)
