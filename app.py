from flask import Flask, render_template, request, redirect, session, jsonify, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "team_task_secret"

DB = "team_task_manager.db"


# ==================================================
# DATABASE
# ==================================================
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT,
            contact TEXT
        )
    """)

    # Projects
    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT,
            description TEXT,
            created_at TEXT
        )
    """)

    # Tasks
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            project_id INTEGER,
            assigned_to INTEGER,
            due_date TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)

    # Default Admin
    admin = cur.execute(
        "SELECT * FROM users WHERE email=?",
        ('admin@gmail.com',)
    ).fetchone()

    if not admin:
        cur.execute("""
            INSERT INTO users(name,email,password,role,contact)
            VALUES(?,?,?,?,?)
        """, (
            'Admin',
            'admin@gmail.com',
            '1234',
            'Admin',
            '9999999999'
        ))

    conn.commit()
    conn.close()


init_db()


# ==================================================
# LOGIN CHECK
# ==================================================
def logged_in():
    return 'user_id' in session


# ==================================================
# LOGIN
# ==================================================
@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        conn = get_db()

        user = conn.execute("""
            SELECT * FROM users
            WHERE email=? AND password=?
        """, (email, password)).fetchone()

        conn.close()

        if user:
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['role'] = user['role']

            if user['role'] == 'Admin':
                return redirect('/admin/dashboard')
            else:
                return redirect('/member/dashboard')

        flash("Invalid Login")

    return render_template('login.html')


# ==================================================
# LOGOUT
# ==================================================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ==================================================
# ADMIN DASHBOARD
# ==================================================
@app.route('/admin/dashboard')
def admin_dashboard():

    if not logged_in() or session['role'] != 'Admin':
        return redirect('/')

    conn = get_db()

    total_projects = conn.execute(
        "SELECT COUNT(*) FROM projects"
    ).fetchone()[0]

    total_members = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role='Member'"
    ).fetchone()[0]

    total_tasks = conn.execute(
        "SELECT COUNT(*) FROM tasks"
    ).fetchone()[0]

    completed_tasks = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE status='Completed'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        'admin/dashboard.html',
        total_projects=total_projects,
        total_members=total_members,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks
    )


# ==================================================
# PROJECTS
# ==================================================
@app.route('/admin/projects', methods=['GET', 'POST'])
def projects():

    if not logged_in() or session['role'] != 'Admin':
        return redirect('/')

    conn = get_db()

    edit_id = request.args.get('edit')
    edit_project = None

    if edit_id:
        edit_project = conn.execute(
            "SELECT * FROM projects WHERE id=?",
            (edit_id,)
        ).fetchone()

    if request.method == 'POST':

        if request.form.get('edit_id'):

            conn.execute("""
                UPDATE projects
                SET project_name=?, description=?
                WHERE id=?
            """, (
                request.form['project_name'],
                request.form['description'],
                request.form['edit_id']
            ))

        else:

            conn.execute("""
                INSERT INTO projects(project_name,description,created_at)
                VALUES(?,?,?)
            """, (
                request.form['project_name'],
                request.form['description'],
                datetime.now().strftime("%Y-%m-%d")
            ))

        conn.commit()
        return redirect('/admin/projects')

    data = conn.execute(
        "SELECT * FROM projects ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        'admin/projects.html',
        projects=data,
        edit_project=edit_project
    )


@app.route('/delete_project/<int:id>')
def delete_project(id):
    conn = get_db()
    conn.execute("DELETE FROM projects WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/admin/projects')


# ==================================================
# MEMBERS
# ==================================================
@app.route('/admin/members', methods=['GET', 'POST'])
def members():

    if not logged_in() or session['role'] != 'Admin':
        return redirect('/')

    conn = get_db()

    edit_id = request.args.get('edit')
    edit_member = None

    if edit_id:
        edit_member = conn.execute(
            "SELECT * FROM users WHERE id=?",
            (edit_id,)
        ).fetchone()

    if request.method == 'POST':

        if request.form.get('edit_id'):

            conn.execute("""
                UPDATE users
                SET name=?, email=?, contact=?, password=?
                WHERE id=?
            """, (
                request.form['name'],
                request.form['email'],
                request.form['contact'],
                request.form['password'],
                request.form['edit_id']
            ))

        else:

            conn.execute("""
                INSERT INTO users(name,email,password,role,contact)
                VALUES(?,?,?,?,?)
            """, (
                request.form['name'],
                request.form['email'],
                request.form['password'],
                'Member',
                request.form['contact']
            ))

        conn.commit()
        return redirect('/admin/members')

    data = conn.execute("""
        SELECT * FROM users
        WHERE role='Member'
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        'admin/members.html',
        members=data,
        edit_member=edit_member
    )


@app.route('/delete_member/<int:id>')
def delete_member(id):
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/admin/members')


# ==================================================
# TASKS
# ==================================================
@app.route('/admin/tasks', methods=['GET', 'POST'])
def tasks():

    if not logged_in() or session['role'] != 'Admin':
        return redirect('/')

    conn = get_db()

    edit_id = request.args.get('edit')
    edit_task = None

    if edit_id:
        edit_task = conn.execute(
            "SELECT * FROM tasks WHERE id=?",
            (edit_id,)
        ).fetchone()

    if request.method == 'POST':

        if request.form.get('edit_id'):

            conn.execute("""
                UPDATE tasks
                SET title=?, project_id=?, assigned_to=?,
                    due_date=?, status=?
                WHERE id=?
            """, (
                request.form['title'],
                request.form['project_id'],
                request.form['assigned_to'],
                request.form['due_date'],
                request.form['status'],
                request.form['edit_id']
            ))

        else:

            conn.execute("""
                INSERT INTO tasks(title,project_id,assigned_to,due_date,status)
                VALUES(?,?,?,?,?)
            """, (
                request.form['title'],
                request.form['project_id'],
                request.form['assigned_to'],
                request.form['due_date'],
                'Pending'
            ))

        conn.commit()
        return redirect('/admin/tasks')

    projects = conn.execute(
        "SELECT * FROM projects"
    ).fetchall()

    members = conn.execute(
        "SELECT * FROM users WHERE role='Member'"
    ).fetchall()

    task_data = conn.execute("""
        SELECT tasks.*,
               projects.project_name,
               users.name
        FROM tasks
        LEFT JOIN projects
        ON tasks.project_id = projects.id
        LEFT JOIN users
        ON tasks.assigned_to = users.id
        ORDER BY tasks.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        'admin/tasks.html',
        tasks=task_data,
        projects=projects,
        members=members,
        edit_task=edit_task
    )


@app.route('/delete_task/<int:id>')
def delete_task(id):
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/admin/tasks')


# ==================================================
# MEMBER DASHBOARD
# ==================================================
@app.route('/member/dashboard')
def member_dashboard():

    if not logged_in() or session['role'] != 'Member':
        return redirect('/')

    uid = session['user_id']

    conn = get_db()

    total = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE assigned_to=?",
        (uid,)
    ).fetchone()[0]

    pending = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE assigned_to=? AND status='Pending'",
        (uid,)
    ).fetchone()[0]

    completed = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE assigned_to=? AND status='Completed'",
        (uid,)
    ).fetchone()[0]

    conn.close()

    return render_template(
        'member/dashboard.html',
        total=total,
        pending=pending,
        completed=completed
    )


# ==================================================
# MEMBER TASK PAGE
# ==================================================
@app.route('/member/tasks', methods=['GET', 'POST'])
def member_tasks():

    if not logged_in() or session['role'] != 'Member':
        return redirect('/')

    uid = session['user_id']
    conn = get_db()

    if request.method == 'POST':

        conn.execute("""
            UPDATE tasks
            SET status=?
            WHERE id=? AND assigned_to=?
        """, (
            request.form['status'],
            request.form['task_id'],
            uid
        ))

        conn.commit()

    data = conn.execute("""
        SELECT tasks.*, projects.project_name
        FROM tasks
        LEFT JOIN projects
        ON tasks.project_id = projects.id
        WHERE assigned_to=?
    """, (uid,)).fetchall()

    conn.close()

    return render_template(
        'member/my_tasks.html',
        tasks=data
    )


# ==================================================
# REST API
# ==================================================
@app.route('/api/projects')
def api_projects():
    conn = get_db()
    data = conn.execute("SELECT * FROM projects").fetchall()
    conn.close()
    return jsonify([dict(x) for x in data])


@app.route('/api/members')
def api_members():
    conn = get_db()
    data = conn.execute("""
        SELECT id,name,email,contact
        FROM users
        WHERE role='Member'
    """).fetchall()
    conn.close()
    return jsonify([dict(x) for x in data])


@app.route('/api/tasks')
def api_tasks():
    conn = get_db()
    data = conn.execute("""
        SELECT * FROM tasks
    """).fetchall()
    conn.close()
    return jsonify([dict(x) for x in data])


# ==================================================
# RUN
# ==================================================
import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)