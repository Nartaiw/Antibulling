from aiohttp import web
import asyncio
import os

async def handle(request):
    return web.Response(text="I am alive!")

async def start_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render берген портты немесе 10000 портты қолданамыз
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server started on port {port}")
