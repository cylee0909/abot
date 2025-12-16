from flask import Flask, jsonify, request
from datetime import date, timedelta
from app.db import init_tables, get_companies_with_details
from app.db.companies import get_company_by_code
from app.db.stock_history import get_history as get_stock_history

def create_app():
    app = Flask(__name__)
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

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5001, debug=False)
