#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import logging
import os
import re
import sqlite3
from collections import defaultdict
from contextlib import closing
from os.path import join, exists
from unittest import expectedFailure

import arrow
from flask import Flask, request, send_from_directory, g, render_template, abort, redirect, url_for
from werkzeug.utils import secure_filename

# from xmind2testcase.utils import get_xmind_testsuites, get_xmind_testcase_list
from xmind2testcase.services import get_testcase_list, count_testsuits
from xmind2testcase.testlink import xmind_to_testlink_xml_file
from xmind2testcase.zentao import xmind_to_zentao_csv_file
from testcase2xmind.parser import parse_zentao_csv
from testcase2xmind.generator import generate_xmind

here = os.path.abspath(os.path.dirname(__file__))
log_file = os.path.join(here, 'running.log')
# log handler
formatter = logging.Formatter('%(asctime)s  %(name)s  %(levelname)s  [%(module)s - %(funcName)s]: %(message)s')
file_handler = logging.FileHandler(log_file, encoding='UTF-8')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)
# xmind to testcase logger
root_logger = logging.getLogger()
root_logger.addHandler(file_handler)
root_logger.addHandler(stream_handler)
root_logger.setLevel(logging.DEBUG)
# flask and werkzeug logger
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.addHandler(file_handler)
werkzeug_logger.addHandler(stream_handler)
werkzeug_logger.setLevel(logging.DEBUG)

# global variable
UPLOAD_FOLDER = os.path.join(here, 'uploads')
ALLOWED_EXTENSIONS = ['xmind', 'csv']
ALLOWED_XMIND_EXTENSIONS = ['xmind']
ALLOWED_CSV_EXTENSIONS = ['csv']
DEBUG = True
DATABASE = os.path.join(here, 'data.db3')
HOST = '0.0.0.0'

# flask app
app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = os.urandom(32)


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def init():
    app.logger.info('Start initializing the database...')
    if not exists(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)

    if not exists(DATABASE):
        app.logger.info('test')
        init_db()
    app.logger.info('Congratulations! the xmind2testcase webtool database has initialized successfully!')


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


def insert_record(xmind_name, note=''):
    c = g.db.cursor()
    now = str(arrow.now())
    sql = "INSERT INTO records (name,create_on,note) VALUES (?,?,?)"
    c.execute(sql, (xmind_name, now, str(note)))
    g.db.commit()


def delete_record(filename, record_id):
    xmind_file = join(app.config['UPLOAD_FOLDER'], filename)
    testlink_file = join(app.config['UPLOAD_FOLDER'], filename[:-5] + 'xml')
    zentao_file = join(app.config['UPLOAD_FOLDER'], filename[:-5] + 'csv')

    for f in [xmind_file, testlink_file, zentao_file]:
        if exists(f):
            os.remove(f)

    c = g.db.cursor()
    sql = 'UPDATE records SET is_deleted=1 WHERE id = ?'
    c.execute(sql, (record_id,))
    g.db.commit()


def delete_records(keep=20):
    """Clean up files on server and mark the record as deleted"""
    sql = "SELECT * from records where is_deleted<>1 ORDER BY id desc LIMIT -1 offset {}".format(keep)
    assert isinstance(g.db, sqlite3.Connection)
    c = g.db.cursor()
    c.execute(sql)
    rows = c.fetchall()
    for row in rows:
        name = row[1]
        xmind_file = join(app.config['UPLOAD_FOLDER'], name)
        testlink_file = join(app.config['UPLOAD_FOLDER'], name[:-5] + 'xml')
        zentao_file = join(app.config['UPLOAD_FOLDER'], name[:-5] + 'csv')

        for f in [xmind_file, testlink_file, zentao_file]:
            if exists(f):
                os.remove(f)

        sql = 'UPDATE records SET is_deleted=1 WHERE id = ?'
        c.execute(sql, (row[0],))
        g.db.commit()


def get_latest_record():
    found = list(get_records(1))
    if found:
        return found[0]


def get_records(limit=8):
    short_name_length = 120
    c = g.db.cursor()
    sql = "select * from records where is_deleted<>1 order by id desc limit {}".format(int(limit))
    c.execute(sql)
    rows = c.fetchall()

    for row in rows:
        name, short_name, create_on, note, record_id = row[1], row[1], row[2], row[3], row[0]

        # shorten the name for display
        if len(name) > short_name_length:
            short_name = name[:short_name_length] + '...'

        # more readable time format
        create_on = arrow.get(create_on).humanize()
        yield short_name, name, create_on, note, record_id


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def allowed_xmind_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_XMIND_EXTENSIONS


def allowed_csv_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_CSV_EXTENSIONS


def insert_csv_record(csv_name, note=''):
    c = g.db.cursor()
    now = str(arrow.now())
    sql = "INSERT INTO csv_records (name,create_on,note) VALUES (?,?,?)"
    c.execute(sql, (csv_name, now, str(note)))
    g.db.commit()


def get_csv_records(limit=8):
    short_name_length = 120
    c = g.db.cursor()
    sql = "select * from csv_records where is_deleted<>1 order by id desc limit {}".format(int(limit))
    c.execute(sql)
    rows = c.fetchall()

    for row in rows:
        name, short_name, create_on, note, record_id = row[1], row[1], row[2], row[3], row[0]
        if len(name) > short_name_length:
            short_name = name[:short_name_length] + '...'
        create_on = arrow.get(create_on).humanize()
        yield short_name, name, create_on, note, record_id


def delete_csv_record(filename, record_id):
    csv_file = join(app.config['UPLOAD_FOLDER'], filename)
    xmind_file = join(app.config['UPLOAD_FOLDER'], filename[:-4] + '.xmind')

    for f in [csv_file, xmind_file]:
        if exists(f):
            os.remove(f)

    c = g.db.cursor()
    sql = 'UPDATE csv_records SET is_deleted=1 WHERE id = ?'
    c.execute(sql, (record_id,))
    g.db.commit()


def save_csv_file(file):
    if file and allowed_csv_file(file.filename):
        filename = file.filename
        upload_to = join(app.config['UPLOAD_FOLDER'], filename)

        if exists(upload_to):
            filename = '{}_{}.csv'.format(filename[:-4], arrow.now().strftime('%Y%m%d_%H%M%S'))
            upload_to = join(app.config['UPLOAD_FOLDER'], filename)

        file.save(upload_to)
        insert_csv_record(filename)
        g.is_success = True
        return filename

    elif file.filename == '':
        g.is_success = False
        g.error = "Please select a file!"

    else:
        g.is_success = False
        g.invalid_files.append(file.filename)


def check_file_name(name):
    secured = secure_filename(name)
    if not secured:
        secured = re.sub(r'[^\w\d]+', '_', name)  # only keep letters and digits from file name
        assert secured, 'Unable to parse file name: {}!'.format(name)
    return secured + '.xmind'


def save_file(file):
    if file and allowed_file(file.filename):
        # filename = check_file_name(file.filename[:-6])
        filename = file.filename
        upload_to = join(app.config['UPLOAD_FOLDER'], filename)

        if exists(upload_to):
            filename = '{}_{}.xmind'.format(filename[:-6], arrow.now().strftime('%Y%m%d_%H%M%S'))
            upload_to = join(app.config['UPLOAD_FOLDER'], filename)

        file.save(upload_to)
        insert_record(filename)
        g.is_success = True
        return filename

    elif file.filename == '':
        g.is_success = False
        g.error = "Please select a file!"

    else:
        g.is_success = False
        g.invalid_files.append(file.filename)


def verify_uploaded_files(files):
    # download the xml directly if only 1 file uploaded
    if len(files) == 1 and getattr(g, 'is_success', False):
        g.download_xml = get_latest_record()[1]

    if g.invalid_files:
        g.error = "Invalid file: {}".format(','.join(g.invalid_files))


@app.route('/', methods=['GET'])
def welcome():
    return render_template('index.html', records=list(get_records()))


@app.route('/xmind2testcase', methods=['GET', 'POST'])
def index(download_xml=None):
    g.invalid_files = []
    g.error = None
    g.download_xml = download_xml
    g.filename = None

    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            return redirect(request.url)

        g.filename = save_file(file)
        verify_uploaded_files([file])
        delete_records()

    else:
        g.upload_form = True

    if g.filename:
        return redirect(url_for('preview_file_v2', filename=g.filename))
    else:
        return render_template('xmind_upload.html', records=list(get_records()))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/<filename>/to/testlink')
def download_testlink_file(filename):
    full_path = join(app.config['UPLOAD_FOLDER'], filename)

    if not exists(full_path):
        abort(404)

    testlink_xmls_file = xmind_to_testlink_xml_file(full_path)
    filename = os.path.basename(testlink_xmls_file) if testlink_xmls_file else abort(404)

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/<filename>/to/zentao')
def download_zentao_file(filename):
    full_path = join(app.config['UPLOAD_FOLDER'], filename)

    if not exists(full_path):
        abort(404)

    zentao_csv_file = xmind_to_zentao_csv_file(full_path)
    filename = os.path.basename(zentao_csv_file) if zentao_csv_file else abort(404)

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/preview/<filename>')
def preview_file(filename):
    full_path = join(app.config['UPLOAD_FOLDER'], filename)

    if not exists(full_path):
        abort(404)
    # suite_count = count_testsuits(full_path)
    testcases = get_testcase_list(full_path)
    test_suites = defaultdict(list)
    for testcase in testcases:
        test_suites[testcase['suite']].append(testcase)

    suite_count = len(test_suites.keys())

    return render_template('preview.html', name=filename, suite=testcases, suite_count=suite_count)


@app.route('/v2/preview/<filename>')
def preview_file_v2(filename):
    full_path = join(app.config['UPLOAD_FOLDER'], filename)

    if not exists(full_path):
        abort(404)

    testcases = get_testcase_list(full_path)
    for testcase in testcases:
        case_name = testcase['name']
        importance = testcase['importance']
        testcase['priority'] = str(importance)

        # 提取所属产品和所属模块
        suite_full = testcase.get('suite', '')
        if '::' in suite_full:
            testcase['product'] = suite_full.split('::', 1)[0]  # 产品名
            testcase['module'] = suite_full.split('::', 1)[1]   # 模块名
        else:
            testcase['product'] = testcase.get('product', '')
            testcase['module'] = suite_full

        category = testcase['category'].replace('<b>', '').replace('</b>', '').replace('<font color="red">',
                                                                                       '').replace('</font>', '')
        testcase['name'] = f"{category}>>{case_name}"
        for step in testcase['steps']:
            expectedresults = step['expectedresults']
            expectedresults_v2 = " && ".join(expectedresults)
            if len(expectedresults) == 0:
                expectedresults_v2 = '-'
            step['expectedresults_v2'] = expectedresults_v2

    test_suites = defaultdict(list)

    for testcase in testcases:
        test_suites[testcase['suite']].append(testcase)

    suite_count = len(test_suites.keys())

    return render_template('preview_v2.html', name=filename, suite=testcases, suite_count=suite_count)


@app.route('/delete/<filename>/<int:record_id>')
def delete_file(filename, record_id):
    full_path = join(app.config['UPLOAD_FOLDER'], filename)
    if not exists(full_path):
        abort(404)
    else:
        delete_record(filename, record_id)
    return redirect(url_for('index'))


@app.route('/testcase2xmind', methods=['GET', 'POST'])
def testcase2xmind_index():
    g.invalid_files = []
    g.error = None
    g.filename = None

    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            return redirect(request.url)

        g.filename = save_csv_file(file)
        delete_records()

    if g.filename:
        return redirect(url_for('testcase2xmind_preview', filename=g.filename))
    else:
        return render_template('testcase2xmind.html', records=list(get_csv_records()))


@app.route('/testcase2xmind/preview/<filename>')
def testcase2xmind_preview(filename):
    full_path = join(app.config['UPLOAD_FOLDER'], filename)

    if not exists(full_path):
        abort(404)

    try:
        encodings = ['utf-8', 'gbk']
        structure = None
        last_error = None
        for enc in encodings:
            try:
                structure = parse_zentao_csv(full_path, encoding=enc)
                if len(structure) > 0:
                    break
            except UnicodeDecodeError as e:
                last_error = e
                continue
        if structure is None or len(structure) == 0:
            raise last_error or Exception("无法解析CSV文件，请检查编码格式")
    except Exception as e:
        return render_template('testcase2xmind_preview.html',
                               name=filename, error=str(e),
                               modules=None, total_cases=0)

    modules = []
    total_cases = 0
    for product, product_modules in structure.items():
        for module_name, cases in product_modules.items():
            case_count = len(cases)
            total_cases += case_count
            modules.append({
                'product': product,
                'name': module_name,
                'case_count': case_count,
                'cases': cases
            })

    return render_template('testcase2xmind_preview.html',
                           name=filename, modules=modules,
                           total_cases=total_cases, error=None)


@app.route('/testcase2xmind/<filename>/to/xmind')
def download_xmind_from_csv(filename):
    full_path = join(app.config['UPLOAD_FOLDER'], filename)

    if not exists(full_path):
        abort(404)

    try:
        encodings = ['utf-8', 'gbk']
        structure = None
        for enc in encodings:
            try:
                structure = parse_zentao_csv(full_path, encoding=enc)
                if len(structure) > 0:
                    break
            except UnicodeDecodeError:
                continue
        if structure is None or len(structure) == 0:
            abort(404)

        output_file = join(app.config['UPLOAD_FOLDER'], filename[:-4] + '.xmind')
        generate_xmind(structure, output_file)
        result_filename = os.path.basename(output_file)
    except Exception as e:
        logging.exception(f'转换CSV到XMind失败: {e}')
        abort(404)

    return send_from_directory(app.config['UPLOAD_FOLDER'], result_filename, as_attachment=True)


@app.route('/testcase2xmind/delete/<filename>/<int:record_id>')
def delete_csv_file(filename, record_id):
    full_path = join(app.config['UPLOAD_FOLDER'], filename)
    if not exists(full_path):
        abort(404)
    else:
        delete_csv_record(filename, record_id)
    return redirect(url_for('testcase2xmind_index'))


@app.errorhandler(Exception)
def app_error(e):
    logging.exception(f'error:{e}')
    return str(e)


def launch(host=HOST, debug=True, port=5001):
    init()  # initializing the database
    app.run(host=host, debug=debug, port=port)


if __name__ == '__main__':
    init()  # initializing the database
    app.run(HOST, debug=DEBUG, port=5002)
