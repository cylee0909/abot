import asyncio
import webbrowser
import argparse
import os
from app.api import create_app

async def run_api(host: str, port: int):
    app = create_app()
    await asyncio.to_thread(app.run, host=host, port=port, debug=False)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--headless', action='store_true', default=True)
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', 5001)))
    parser.add_argument('--host', type=str, default=os.environ.get('HOST', '127.0.0.1'))
    args = parser.parse_args()
    server_task = asyncio.create_task(run_api(args.host, args.port))
    if not args.headless:
        await asyncio.sleep(1)
        webbrowser.open(f'http://{args.host}:{args.port}/')
    await server_task

if __name__ == '__main__':
    asyncio.run(main())
