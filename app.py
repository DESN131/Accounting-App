from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib import font_manager
import io
import base64
import os

# 设置 Matplotlib 使用中文字体
# plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
# plt.rcParams['font.family'] = 'Microsoft YaHei'
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "database.db")

# 初始化数据库
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS entries (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            date TEXT,
                            description TEXT,
                            amount REAL,
                            type TEXT,
                            currency TEXT DEFAULT 'AUD',
                            category TEXT
                        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS categories (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT UNIQUE NOT NULL
                        )''')
        conn.commit()

init_db()

# 分别生成收入和支出的图表
def generate_chart():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT date, SUM(amount), type FROM entries GROUP BY date ORDER BY date")
        entries = cursor.fetchall()

    dates = [entry[0] for entry in entries]
    income = [entry[1] if entry[2] == 'income' else 0 for entry in entries]
    expense = [entry[1] if entry[2] == 'expense' else 0 for entry in entries]

    # 绘制图表
    plt.figure(figsize=(10, 7))
    plt.plot(dates, income, marker='o', label="Income", color="green")
    plt.plot(dates, expense, marker='o', label="Expense", color="red")
    plt.title("Income and Expense Records")
    plt.xlabel("Date")
    plt.ylabel("Amount")
    plt.xticks(rotation=45)
    plt.legend()

    # 保存图表到内存
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode()
    return chart_url

@app.route('/')
def index():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entries ORDER BY date DESC")
        entries = cursor.fetchall()
        # 计算总支出（只包含类型为 'expense' 的条目）
        total_expense = round(sum(entry[3] for entry in entries if entry[4] == 'expense'), 2)

    chart_url = generate_chart()
    return render_template("index.html", entries=entries, total_expense=total_expense, chart_url=chart_url)


@app.route('/add', methods=["GET", "POST"])
def add_entry():
    if request.method == "POST":
        date = request.form.get("date") or datetime.now().strftime('%Y-%m-%d')
        description = request.form.get("description")
        amount = request.form.get("amount")
        type = request.form.get("type")
        currency = request.form.get("currency") or 'AUD'
        category = request.form.get("category")

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO entries (date, description, amount, type, currency, category) VALUES (?, ?, ?, ?, ?, ?)",
                           (date, description, amount, type, currency, category))
            conn.commit()
        return redirect(url_for('index'))

    today = datetime.now().strftime('%Y-%m-%d')
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM categories")
        categories = [row[0] for row in cursor.fetchall()]
    return render_template("add_entry.html", today=today, categories=categories)

@app.route('/edit/<int:id>', methods=["GET", "POST"])
def edit_entry(id):
    if request.method == "POST":
        date = request.form.get("date")
        description = request.form.get("description")
        amount = request.form.get("amount")
        type = request.form.get("type")
        currency = request.form.get("currency")
        category = request.form.get("category")

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE entries SET date=?, description=?, amount=?, type=?, currency=?, category=? WHERE id=?",
                           (date, description, amount, type, currency, category, id))
            conn.commit()
        return redirect(url_for('index'))

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entries WHERE id=?", (id,))
        entry = cursor.fetchone()

        cursor.execute("SELECT name FROM categories")
        categories = [row[0] for row in cursor.fetchall()]
    return render_template("edit_entry.html", entry=entry, categories=categories)

@app.route('/categories', methods=["GET", "POST"])
def manage_categories():
    if request.method == "POST":
        category_name = request.form.get("category_name")
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
                conn.commit()
            except sqlite3.IntegrityError:
                pass  # Ignore if category already exists
        return redirect(url_for('manage_categories'))

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories")
        categories = cursor.fetchall()
    
    return render_template("manage_categories.html", categories=categories)

@app.route('/delete_category/<int:id>', methods=["POST"])
def delete_category(id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE id=?", (id,))
        conn.commit()
    return redirect(url_for('manage_categories'))

@app.route('/delete_entry/<int:id>', methods=["POST"])
def delete_entry(id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM entries WHERE id=?", (id,))
        conn.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

