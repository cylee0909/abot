import sqlite3
from flask import Flask, jsonify, request, send_file
from datetime import date, timedelta
from pathlib import Path
from app.db import init_tables, get_companies_with_details
from app.db.connection import db
from app.db.companies import get_company_by_code
from app.db.stock_history import get_history as get_stock_history
from app.db.stock_groups import (
    create_group, delete_group, get_all_groups, get_group_by_id,
    add_stock_to_group, remove_stock_from_group, get_stocks_in_group,
    get_stocks_in_group_with_details, get_groups_for_stock
)

DIST_DIR = (Path(__file__).resolve().parents[2] / 'frontend' / 'dist')
ASSETS_DIR = DIST_DIR / 'assets'

def create_app():
    app = Flask(__name__, static_folder=str(DIST_DIR))
    init_tables()

    @app.after_request
    def add_cors(resp):
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET,OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp

    @app.route('/companies', methods=['GET'])
    def companies():
        data = get_companies_with_details()
        return jsonify({'data': data, 'count': len(data)})

    @app.route('/companies/<security_code>', methods=['GET'])
    def company(security_code):
        item = get_company_by_code(security_code)
        if item is None:
            return jsonify({'error': 'not found'}), 404
        return jsonify(item)

    @app.route('/history/<stock_code>', methods=['GET'])
    def history(stock_code):
        start = request.args.get('start')
        end = request.args.get('end')
        limit = request.args.get('limit', type=int)

        if not start and not end:
            start = (date.today() - timedelta(days=365 * 3)).strftime('%Y-%m-%d')
            # 可选：如需限定上限日期
            # end = date.today().strftime('%Y-%m-%d')
        code = stock_code.split('.')[:1][0]
        data = get_stock_history(code, start_date=start, end_date=end, limit=limit)
        return jsonify({'data': data, 'count': len(data)})

    @app.route('/', methods=['GET'])
    def index():
        resp = send_file(Path(app.static_folder) / 'index.html')
        resp.headers['Cache-Control'] = 'no-cache'
        return resp

    @app.route('/assets/<path:filename>', methods=['GET'])
    def assets(filename):
        p = ASSETS_DIR / filename
        if not p.is_file():
            return jsonify({'error': 'not found'}), 404
        resp = send_file(p)
        resp.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        return resp

    @app.route('/<path:path>', methods=['GET'])
    def spa_fallback(path):
        p = Path(app.static_folder) / path
        if p.is_file():
            if p.suffix == '.html':
                resp = send_file(p)
                resp.headers['Cache-Control'] = 'no-cache'
                return resp
            resp = send_file(p)
            resp.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            return resp
        resp = send_file(Path(app.static_folder) / 'index.html')
        resp.headers['Cache-Control'] = 'no-cache'
        return resp
    
    # 股票分组相关API
    @app.route('/groups', methods=['GET', 'POST'])
    def groups():
        if request.method == 'GET':
            # 获取所有分组
            data = get_all_groups()
            return jsonify({'data': data, 'count': len(data)})
        elif request.method == 'POST':
            # 创建新分组
            data = request.get_json()
            if not data or 'name' not in data:
                return jsonify({'error': 'Missing group name'}), 400
            
            group_name = data['name']
            
            # 调用create_group函数创建分组
            group_id = create_group(group_name)
            
            if group_id > 0:
                # 创建成功
                return jsonify({'id': group_id, 'name': group_name}), 201
            
            # 创建失败，检查是否是分组名称已存在
            existing_groups = get_all_groups()
            if any(group['name'] == group_name for group in existing_groups):
                return jsonify({'error': 'Group name already exists'}), 409
            
            # 其他未知错误
            return jsonify({'error': 'Failed to create group'}), 500
    
    @app.route('/groups/<int:group_id>', methods=['DELETE'])
    def delete_group_api(group_id):
        # 删除分组
        success = delete_group(group_id)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Failed to delete group'}), 500
    
    @app.route('/groups/<int:group_id>/stocks', methods=['GET', 'POST', 'DELETE'])
    def group_stocks(group_id):
        if request.method == 'GET':
            # 获取分组中的所有股票
            include_details = request.args.get('details', 'false').lower() == 'true'
            if include_details:
                data = get_stocks_in_group_with_details(group_id)
            else:
                data = get_stocks_in_group(group_id)
            return jsonify({'data': data, 'count': len(data)})
        elif request.method == 'POST':
            # 将股票添加到分组
            data = request.get_json()
            if not data or 'stock_code' not in data:
                return jsonify({'error': 'Missing stock_code'}), 400
            success = add_stock_to_group(group_id, data['stock_code'])
            if success:
                return jsonify({'success': True}), 201
            return jsonify({'error': 'Failed to add stock to group'}), 500
    
    @app.route('/groups/<int:group_id>/stocks/<stock_code>', methods=['DELETE'])
    def remove_group_stock(group_id, stock_code):
        # 从分组中移除股票
        success = remove_stock_from_group(group_id, stock_code)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Failed to remove stock from group'}), 500
    
    @app.route('/stocks/<stock_code>/groups', methods=['GET'])
    def stock_groups(stock_code):
        # 获取股票所属的所有分组
        data = get_groups_for_stock(stock_code)
        return jsonify({'data': data, 'count': len(data)})

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5001, debug=False)
