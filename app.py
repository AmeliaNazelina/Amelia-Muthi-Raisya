from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'  # Untuk flash messages

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Model Task
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    deadline = db.Column(db.Date, nullable=True)
    position = db.Column(db.Integer, nullable=False, default=0)  # Tambahkan kolom posisi

@app.route('/')
def index():
    tasks = Task.query.order_by(Task.position.asc()).all()  # Urutkan berdasarkan posisi
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add():
    task_content = request.form.get('content', '').strip()
    deadline_str = request.form.get('deadline', '').strip()

    if not task_content:
        flash("Tugas belum ditambahkan", "error")
        return redirect(url_for('index'))  # Mencegah input kosong

    # Validasi deadline tidak boleh di masa lalu
    if deadline_str:
        try:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
            if deadline < datetime.today().date():
                flash("Tenggat waktu harus pada tanggal yang belum terlewat!", "error")
                return redirect(url_for('index'))
        except ValueError:
            flash("Format tanggal tidak valid!", "error")
            return redirect(url_for('index'))
    else:
        deadline = None

    # Hitung posisi terakhir
    last_task = Task.query.order_by(Task.position.desc()).first()
    new_position = (last_task.position + 1) if last_task else 0

    new_task = Task(content=task_content, deadline=deadline, position=new_position)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete(id):
    task = Task.query.get(id)
    if task:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['POST'])
def edit(id):
    task = Task.query.get(id)
    if task:
        task.content = request.form.get('content', task.content).strip()
        deadline_str = request.form.get('deadline', '').strip()
        
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
                if deadline < datetime.today().date():
                    flash("Tenggat waktu harus pada tanggal yang belum terlewat!", "error")
                    return redirect(url_for('index'))
                task.deadline = deadline
            except ValueError:
                flash("Format tanggal tidak valid!", "error")
                return redirect(url_for('index'))
        
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/update-order', methods=['POST'])
def update_order():
    data = request.get_json()
    for item in data['order']:
        task = Task.query.get(item['id'])
        if task:
            task.position = item['position']
    db.session.commit()
    return jsonify({"message": "Order updated"}), 200

if __name__ == '__main__':
    app.run(debug=True)
