from flask import Flask, request, redirect, render_template, session
import psycopg2
import os
import uuid

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "mydb"),
        user=os.getenv("DB_USER", "myuser"),
        password=os.getenv("DB_PASSWORD", "")
    )
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            description TEXT NOT NULL,
            completed BOOLEAN DEFAULT FALSE,
            user_id TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    cur = conn.cursor()

    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())

    user_id = session['user_id']

    if request.method == 'POST':
        task_description = request.form['task']
        cur.execute("INSERT INTO tasks (description, user_id) VALUES (%s, %s)", (task_description, user_id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect('/')

    cur.execute("SELECT * FROM tasks WHERE user_id = %s", (user_id,))
    tasks = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('index.html', tasks=tasks)

@app.route('/complete/<int:id>')
def complete_task(id):
    if 'user_id' not in session:
        return redirect('/')
    
    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("UPDATE tasks SET completed = TRUE WHERE id = %s AND user_id = %s", (id, user_id))
        conn.commit()
        print(f"[DEBUG] Updated task {id} for user {user_id}, rows affected: {cur.rowcount}")
        if cur.rowcount == 0:
            print(f"[WARNING] Task {id} not found or does not belong to user {user_id}")
    except Exception as e:
        print(f"[ERROR] Failed to update task {id}: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

    return redirect('/')

@app.route('/delete/<int:id>')
def delete_task(id):
    if 'user_id' not in session:
        return redirect('/')

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", (id, user_id))
        conn.commit()
        print(f"[DEBUG] Deleted task {id}, rows affected: {cur.rowcount}")
        if cur.rowcount == 0:
            print(f"[WARNING] Task {id} not found or does not belong to user {user_id}")
    except Exception as e:
        print(f"[ERROR] Failed to delete task {id}: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

    return redirect('/')

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=5000)
