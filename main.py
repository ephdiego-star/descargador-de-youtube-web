import os
import yt_dlp
import requests as req_lib
from flask import Flask, render_template_string, request, Response

app = Flask(__name__)

COOKIES_PATH = '/tmp/cookies.txt'

PAGINA_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Descargador de YouTube Web</title>
    <style>
        :root { --bg: #121212; --text: #ffffff; --card: #1e1e1e; --primary: #3b82f6; }
        body { font-family: 'Segoe UI', sans-serif; background-color: var(--bg); color: var(--text); display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .container { background: var(--card); padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); text-align: center; width: 90%; max-width: 500px; }
        h1 { font-size: 24px; margin-bottom: 20px; color: var(--primary); }
        input[type="text"] { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #333; background: #2a2a2a; color: #fff; box-sizing: border-box; margin-bottom: 15px; font-size: 14px; }
        button { background: var(--primary); color: white; border: none; padding: 12px 20px; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; width: 100%; transition: background 0.2s; }
        button:hover { background: #2563eb; }
        .footer { margin-top: 20px; font-size: 12px; color: #888; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📥 Descargador Web Inteligente</h1>
        <form action="/descargar" method="GET">
            <input type="text" name="url" placeholder="Pega el enlace de YouTube aquí..." required>
            <button type="submit">Descargar Video</button>
        </form>
        <div class="footer">Funciona en Celulares, Tablets y PCs - Calidad Estándar</div>
    </div>
</body>
</html>
"""

@app.route('/')
def inicio():
    return render_template_string(PAGINA_HTML)

@app.route('/debug')
def debug():
    cookies_content = os.environ.get('YOUTUBE_COOKIES')
    if not cookies_content:
        return "YOUTUBE_COOKIES no existe", 200
    with open(COOKIES_PATH, 'w') as f:
        f.write(cookies_content)
    return f"Cookies escritas. Longitud: {len(cookies_content)} chars. Primeras 100: {cookies_content[:100]}", 200

@app.route('/descargar')
def descargar():
    video_url = request.args.get('url')
    if not video_url:
        return "Por favor, introduce una URL válida.", 400

    cookies_content = os.environ.get('YOUTUBE_COOKIES')
    if cookies_content:
        with open(COOKIES_PATH, 'w') as f:
            f.write(cookies_content)

    opciones = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        'outtmpl': '/tmp/%(id)s.%(ext)s',
    }

    if os.path.exists(COOKIES_PATH):
        opciones['cookiefile'] = COOKIES_PATH

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(video_url, download=True)

        video_id = info.get('id')
        titulo = info.get('title', 'video').replace('/', '-')
        archivo = f'/tmp/{video_id}.mp4'

        if not os.path.exists(archivo):
            # Si no existe como .mp4, buscar cualquier archivo con ese ID
            import glob
            archivos = glob.glob(f'/tmp/{video_id}.*')
            if archivos:
                archivo = archivos[0]
            else:
                return "No se pudo generar el archivo.", 500

        def generar():
            with open(archivo, 'rb') as f:
                while chunk := f.read(1024 * 256):
                    yield chunk
            os.remove(archivo)

        # Obtener la extensión real del archivo
        ext = archivo.split('.')[-1]
        
        return Response(
            generar(),
            content_type=f'video/{ext}',
            headers={
                'Content-Disposition': f'attachment; filename="{titulo}.{ext}"',
            }
        )

    except Exception as e:
        return f"Error al procesar el video: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
