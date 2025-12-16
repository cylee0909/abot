import asyncio
import webbrowser
import argparse
from app.api import create_app

async def run_api():
    app = create_app()
    await asyncio.to_thread(app.run, host='127.0.0.1', port=5001, debug=False)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--headless', action='store_true')
    args = parser.parse_args()
    server_task = asyncio.create_task(run_api())
    if not args.headless:
        await asyncio.sleep(1)
        webbrowser.open('http://127.0.0.1:5001/')
    await server_task

if __name__ == '__main__':
    asyncio.run(main())
