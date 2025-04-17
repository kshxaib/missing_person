from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///missing_persons.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)

class MissingPerson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    last_seen = db.Column(db.String(200), nullable=False)
    date_missing = db.Column(db.Date)
    description = db.Column(db.Text)
    contact = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(100))
    status = db.Column(db.String(20), default='Missing')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    recent_persons = MissingPerson.query.filter_by(status='Missing').order_by(MissingPerson.date_missing.desc()).limit(6).all()
    return render_template('index.html', recent_persons=recent_persons)

@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form.get('gender')
        last_seen = request.form['last_seen']
        date_missing = request.form.get('date')
        description = request.form['description']
        contact = request.form['contact']

        image = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image = filename

        new_person = MissingPerson(
            name=name,
            age=age,
            gender=gender,
            last_seen=last_seen,
            date_missing=datetime.strptime(date_missing, '%Y-%m-%d'),
            description=description,
            contact=contact,
            image=image
        )

        db.session.add(new_person)
        db.session.commit()

        flash('Missing person report submitted successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('report.html')

@app.route('/person/<int:id>')
def person_detail(id):
    person = MissingPerson.query.get_or_404(id)
    return render_template('person_detail.html', person=person)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    results = []
    if query:
        results = MissingPerson.query.filter(
            (MissingPerson.name.contains(query)) |
            (MissingPerson.description.contains(query))
        ).filter_by(status='Missing').all()
    return render_template('search.html', results=results, query=query)

@app.route('/admin/mark_found/<int:id>')
def mark_found(id):
    person = MissingPerson.query.get_or_404(id)
    person.status = 'Found'
    db.session.commit()
    flash(f'{person.name} has been marked as found!', 'success')
    return redirect(url_for('person_detail', id=id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
