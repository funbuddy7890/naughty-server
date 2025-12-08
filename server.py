import os
import asyncio
from telethon import TelegramClient
from aiohttp import web

# ================= CONFIGURATION =================
API_ID = 39394783
API_HASH = 'ea9e02373562fa1b888cee955f66e35a'
BOT_TOKEN = '8000177324:AAHISycS0-YiiEAbMDsXA3X4ZD-l3xvZdg0'
CHANNEL_USERNAME = 'naughtyfilter' 

# RENDER CONFIG
PORT = int(os.environ.get("PORT", 8080))
HOST = '0.0.0.0'
# =================================================

client = TelegramClient('telibot_session', API_ID, API_HASH)

async def start_telegram(app):
    print(f"--- RENDER SERVER STARTING ---")
    await client.start(bot_token=BOT_TOKEN)
    print(f"✅ Bot Connected! Reading @{CHANNEL_USERNAME}")

async def stop_telegram(app):
    await client.disconnect()

async def root_handler(request):
    return web.Response(text="Naughty Filter Server is Running on Render!", content_type='text/html')

# --- NEW: VERIFICATION HANDLER ---
async def verify_handler(request):
    # This matches the filename ExoClick gave you
    return web.FileResponse('./e81f9868d1f9f7695b60002f873ed95f.html')

async def stream_handler(request):
    try:
        msg_id = int(request.match_info['msg_id'])
        
        try:
            message = await client.get_messages(CHANNEL_USERNAME, ids=msg_id)
        except:
            return web.Response(status=404, text="Channel not found")

        if not message or not message.file:
            return web.Response(status=404, text="Video not found")

        file_size = message.file.size
        mime_type = 'video/mp4' 
        
        range_header = request.headers.get('Range')
        offset, length = 0, file_size
        status_code = 200

        if range_header:
            parts = range_header.replace('bytes=', '').split('-')
            offset = int(parts[0])
            if parts[1]: length = int(parts[1]) - offset + 1
            else: length = file_size - offset
            status_code = 206

        response = web.StreamResponse(
            status=status_code,
            headers={
                'Content-Type': mime_type,
                'Content-Range': f'bytes {offset}-{offset + length - 1}/{file_size}',
                'Content-Length': str(length),
                'Accept-Ranges': 'bytes',
                'Access-Control-Allow-Origin': '*' 
            }
        )
        await response.prepare(request)
        
        async for chunk in client.iter_download(message.media, offset=offset, chunk_size=131072):
            await response.write(chunk)
            
        return response

    except Exception as e:
        print(f"Error: {e}")
        return web.Response(status=500, text=str(e))

app = web.Application()
app.router.add_get('/', root_handler)

# --- NEW: ADD THE VERIFICATION ROUTE ---
# This tells the server: "When someone asks for this file, show it to them"
app.router.add_get('/e81f9868d1f9f7695b60002f873ed95f.html', verify_handler)

app.router.add_get('/stream/{msg_id}', stream_handler)
app.on_startup.append(start_telegram)
app.on_cleanup.append(stop_telegram)

if __name__ == '__main__':
    web.run_app(app, host=HOST, port=PORT)
