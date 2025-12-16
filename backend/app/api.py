from flask import Flask, jsonify, request, send_file
from datetime import date, timedelta
from pathlib import Path
from app.db import init_tables, get_companies_with_details
from app.db.companies import get_company_by_code
from app.db.stock_history import get_history as get_stock_history

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

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5001, debug=False)
