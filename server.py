import sqlite3
import os
import html
import re
from flask import Flask, request, jsonify, render_template, session, redirect, flash
from functools import wraps

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'super_secret_key_for_admin_login'  # Для flash()

DB = 'patp.db'
UPLOAD_FOLDER = 'static/images'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# === Декоратор для защиты админки ===
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin'):
            return redirect("/admin/login")
        return f(*args, **kwargs)
    return decorated_function


# === Инициализация БД ===
def init_db():
    with app.app_context():
        db = sqlite3.connect(DB)
        cur = db.cursor()

        # --- Таблица новостей ---
        cur.execute('''CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            image TEXT NOT NULL,
            date TEXT NOT NULL
        )''')

        # --- Таблица администраторов ---
        cur.execute('''CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )''')

        # --- Заявки на работу ---
        cur.execute('''CREATE TABLE IF NOT EXISTS job_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT NOT NULL,
            message TEXT,
            status TEXT DEFAULT "новое"
        )''')

        # --- Заявки на оказание услуг ---
        cur.execute('''CREATE TABLE IF NOT EXISTS service_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT NOT NULL,
            service_type TEXT NOT NULL,
            message TEXT,
            status TEXT DEFAULT "новое"
        )''')

        # --- Тестовый админ ---
        try:
            cur.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ('admin', 'admin123'))
        except sqlite3.IntegrityError:
            pass  # Уже существует

        db.commit()
        db.close()


# --- Получение новости по ID ---
def get_news_by_id(news_id):
    try:
        db = sqlite3.connect(DB)
        cursor = db.cursor()
        cursor.execute("SELECT * FROM news WHERE id = ?", (news_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': row[0],
            'title': row[1],
            'description': row[2],
            'image': row[3],
            'date': row[4]
        }
    finally:
        db.close()


# --- Авторизация в админке ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        db = sqlite3.connect(DB)
        cur = db.cursor()
        cur.execute("SELECT * FROM admins WHERE username = ? AND password = ?", (username, password))
        user = cur.fetchone()
        db.close()

        if user:
            session['admin'] = True
            return redirect("/admin/dashboard")

        return render_template("admin/login.html", error="Неверный логин или пароль")

    return render_template("admin/login.html")


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect("/admin/login")


# --- Админка: дашборд ---
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    db = sqlite3.connect(DB)
    cur = db.cursor()

    cur.execute("SELECT id, name, phone, status FROM job_applications")
    job_applications = cur.fetchall()

    cur.execute("SELECT id, name, phone, service_type, status FROM service_requests")
    service_requests = cur.fetchall()

    cur.execute("SELECT id, title, date FROM news")
    news_list = cur.fetchall()

    db.close()

    return render_template("admin/dashboard.html",
                           job_applications=job_applications,
                           service_requests=service_requests,
                           news_list=news_list)


# --- Заявки на работу ---
@app.route('/admin/job-applications')
@login_required
def admin_job_applications():
    db = sqlite3.connect(DB)
    cur = db.cursor()
    cur.execute("SELECT id, name, email, phone, message, status FROM job_applications")
    applications = cur.fetchall()
    db.close()
    return render_template("admin/job_applications.html", applications=applications)


@app.route('/admin/job/status/<int:id>', methods=['POST'])
@login_required
def update_job_status(id):
    new_status = request.form.get('status')
    db = sqlite3.connect(DB)
    cur = db.cursor()
    cur.execute("UPDATE job_applications SET status = ? WHERE id = ?", (new_status, id))
    db.commit()
    db.close()
    return '', 204


# --- Заявки на оказание услуг ---
@app.route('/admin/service-requests')
@login_required
def admin_service_requests():
    db = sqlite3.connect(DB)
    cur = db.cursor()
    cur.execute("SELECT id, name, phone, service_type, status FROM service_requests")
    requests = cur.fetchall()
    db.close()
    return render_template("admin/service_requests.html", requests=requests)


@app.route('/admin/service/status/<int:id>', methods=['POST'])
@login_required
def update_service_status(id):
    new_status = request.form.get('status')
    db = sqlite3.connect(DB)
    cur = db.cursor()
    cur.execute("UPDATE service_requests SET status = ? WHERE id = ?", (new_status, id))
    db.commit()
    db.close()
    return '', 204


# --- Управление новостями ---
@app.route('/admin/news')
@login_required
def admin_news_list():
    db = sqlite3.connect(DB)
    cur = db.cursor()
    cur.execute("SELECT id, title, date, image FROM news ORDER BY id DESC")
    news_list = cur.fetchall()
    db.close()
    return render_template("admin/news_list.html", news_list=news_list)


@app.route('/admin/news/add', methods=['GET', 'POST'])
@login_required
def admin_add_news():
    if request.method == 'POST':
        title = html.escape(request.form.get('title'))
        description = html.escape(request.form.get('description'))
        date = html.escape(request.form.get('date'))

        # Проверка даты
        if not re.match(r'^\d{2}/\d{2}/\d{4}$', date):
            flash("Дата должна быть в формате дд/мм/гггг")
            return redirect("/admin/news/add")

        # Загрузка изображения
        file = request.files.get('image')
        image_path = html.escape(request.form.get('image_path', ''))

        if file and file.filename != '':
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = f'/static/images/{filename}'
        elif not image_path:
            flash("Изображение обязательно")
            return redirect("/admin/news/add")

        try:
            db = sqlite3.connect(DB)
            cur = db.cursor()
            cur.execute('''
                INSERT INTO news (title, description, image, date) VALUES (?, ?, ?, ?)
            ''', (title, description, image_path, date))
            db.commit()
            return redirect('/admin/news')
        except Exception as e:
            db.rollback()
            flash("Ошибка при добавлении новости")
            return redirect("/admin/news/add")
        finally:
            db.close()

    return render_template("admin/news_add.html")


@app.route('/admin/news/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_news(id):
    db = sqlite3.connect(DB)
    cur = db.cursor()

    if request.method == 'POST':
        title = html.escape(request.form.get('title'))
        description = html.escape(request.form.get('description'))
        date = html.escape(request.form.get('date'))
        image_path = html.escape(request.form.get('image_path', ''))

        # Если загружено новое изображение
        file = request.files.get('image')
        if file and file.filename != '':
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = f'/static/images/{filename}'
        else:
            # Сохраняем текущее изображение, если новое не указано
            cur.execute("SELECT image FROM news WHERE id = ?", (id,))
            current_image = cur.fetchone()[0]
            image_path = current_image

        cur.execute("UPDATE news SET title=?, description=?, image=?, date=? WHERE id=?",
                    (title, description, image_path, date, id))
        db.commit()
        db.close()
        return redirect('/admin/news')

    cur.execute("SELECT * FROM news WHERE id = ?", (id,))
    news = cur.fetchone()
    db.close()

    return render_template("admin/news_edit.html", news=news)


@app.route('/admin/news/delete/<int:id>')
@login_required
def admin_delete_news(id):
    db = sqlite3.connect(DB)
    cur = db.cursor()
    cur.execute("DELETE FROM news WHERE id=?", (id,))
    db.commit()
    db.close()
    return redirect('/admin/news')


# --- Форма: отправка заявки на работу ---
@app.route('/send-job', methods=['POST'])
def send_job_application():
    name = html.escape(request.form.get('job-name'))
    email = html.escape(request.form.get('job-email'))
    phone = html.escape(request.form.get('job-phone'))
    message = html.escape(request.form.get('job-message'))

    if not name or not phone or not message:
        flash("Все обязательные поля должны быть заполнены")
        return redirect("/support")

    try:
        db = sqlite3.connect(DB)
        cur = db.cursor()
        cur.execute('''
            INSERT INTO job_applications (name, email, phone, message)
            VALUES (?, ?, ?, ?)
        ''', (name, email, phone, message))
        db.commit()
        flash("Заявка на работу успешно отправлена!")
    except Exception as e:
        db.rollback()
        flash("Ошибка при отправке заявки на работу")
    finally:
        db.close()

    return redirect("/support")


# --- Форма: отправка заявки на услугу ---
@app.route('/send', methods=['POST'])
def send_service_request():
    name = html.escape(request.form.get('name'))
    email = html.escape(request.form.get('email'))
    telephone = html.escape(request.form.get('telephone'))
    service_type = html.escape(request.form.get('service'))
    message = html.escape(request.form.get('message'))

    if not name or not telephone or not service_type or not message:
        flash("Все обязательные поля должны быть заполнены")
        return redirect("/support")

    try:
        db = sqlite3.connect(DB)
        cur = db.cursor()
        cur.execute('''
            INSERT INTO service_requests (name, email, phone, service_type, message)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, email, telephone, service_type, message))
        db.commit()
        flash("Заявка на услугу успешно отправлена!")
    except Exception as e:
        db.rollback()
        flash("Ошибка при отправке заявки на услугу")
    finally:
        db.close()

    return redirect("/support")


# --- Основные страницы сайта ---
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/news')
def news_page():
    return render_template('news.html')


@app.route('/single-news/<int:news_id>')
def single_news_page(news_id):
    news = get_news_by_id(news_id)
    if news:
        return render_template('single-news.html', news=news)
    else:
        return render_template('404.html'), 404


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/about-us')
def about_us():
    return render_template('about-us.html')


@app.route('/documents')
def documents():
    return render_template('documents.html')


@app.route('/service')
def service():
    return render_template('service.html')


@app.route('/charter')
def charter():
    return render_template('charter.html')


@app.route('/passenger')
def passenger():
    return render_template('passenger.html')


@app.route('/children')
def children():
    return render_template('children.html')


@app.route('/payment')
def payment():
    return render_template('payment.html')


@app.route('/price')
def price():
    return render_template('price.html')


@app.route('/schedule')
def schedule():
    return render_template('schedule.html')


@app.route('/your-ticket')
def your_ticket():
    return render_template('your-ticket.html')


@app.route('/official-information')
def official_information():
    return render_template('official-information.html')


@app.route('/anti-corruption')
def anti_corruption():
    return render_template('anti-corruption.html')


@app.route('/work')
def work():
    return render_template('work.html')


@app.route('/support')
def support():
    return render_template('support.html')


# --- API для новостей ---
@app.route('/api/news', methods=['GET'])
def get_news():
    page = int(request.args.get('page', 1))
    limit = 4
    offset = (page - 1) * limit

    try:
        db = sqlite3.connect(DB)
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM news")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT * FROM news ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset))
        rows = cursor.fetchall()

        news_list = [{'id': r[0], 'title': r[1], 'description': r[2], 'image': r[3], 'date': r[4]} for r in rows]

        return jsonify({
            'news': news_list,
            'total': total,
            'per_page': limit,
            'current_page': page
        })
    finally:
        db.close()


@app.route('/api/news/all', methods=['GET'])
def get_all_news():
    try:
        db = sqlite3.connect(DB)
        cursor = db.cursor()
        cursor.execute("SELECT * FROM news ORDER BY id DESC")
        rows = cursor.fetchall()
        return jsonify([{'id': r[0], 'title': r[1], 'description': r[2], 'image': r[3], 'date': r[4]} for r in rows])
    finally:
        db.close()


@app.route('/api/news/<int:news_id>', methods=['GET'])
def get_single_news(news_id):
    news = get_news_by_id(news_id)
    if news:
        return jsonify(news)
    else:
        return jsonify({'error': 'Новость не найдена'}), 404


@app.route('/api/news', methods=['POST'])
def add_news_api():
    title = html.escape(request.form.get('title'))
    description = html.escape(request.form.get('description'))
    date = html.escape(request.form.get('date'))

    if not re.match(r'^\d{2}/\d{2}/\d{4}$', date):
        return jsonify({'error': 'Дата должна быть в формате дд/мм/гггг'}), 400

    file = request.files.get('image')
    if file and file.filename != '':
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_path = f'/static/images/{filename}'
    else:
        image_path = html.escape(request.form.get('image_path', ''))
        if not image_path:
            return jsonify({'error': 'Изображение обязательно'}), 400

    try:
        db = sqlite3.connect(DB)
        cur = db.cursor()
        cur.execute('''
            INSERT INTO news (title, description, image, date) VALUES (?, ?, ?, ?)
        ''', (title, description, image_path, date))
        db.commit()
        return jsonify({'success': True, 'id': cur.lastrowid}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/news/<int:news_id>', methods=['PUT'])
def update_news_api(news_id):
    title = html.escape(request.form.get('title'))
    description = html.escape(request.form.get('description'))
    date = html.escape(request.form.get('date'))

    if not re.match(r'^\d{2}/\d{2}/\d{4}$', date):
        return jsonify({'error': 'Дата должна быть в формате дд/мм/гггг'}), 400

    file = request.files.get('image')
    image_path = html.escape(request.form.get('image_path', ''))

    if file and file.filename != '':
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_path = f'/static/images/{filename}'
    elif not image_path:
        return jsonify({'error': 'Изображение обязательно'}), 400

    try:
        db = sqlite3.connect(DB)
        cursor = db.cursor()
        cursor.execute('''
            UPDATE news SET title=?, description=?, image=?, date=? WHERE id=?
        ''', (title, description, image_path, date, news_id))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/news/<int:news_id>', methods=['DELETE'])
def delete_news_api(news_id):
    try:
        db = sqlite3.connect(DB)
        cursor = db.cursor()
        cursor.execute("DELETE FROM news WHERE id = ?", (news_id,))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


# --- Страница ошибок ---
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)