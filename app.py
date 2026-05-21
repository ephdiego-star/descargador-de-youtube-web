import os
import yt_dlp
from flask import Flask, render_template_string, request, Response
import requests as req_lib

app = Flask(__name__)
PAGINA_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Descargador de YouTube Web</title>
    <style>
        :root { 
            --bg: #121212; 
            --text: #ffffff; 
            --card: #1e1e1e; 
            --primary: #3b82f6; 
        }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background-color: var(--bg); 
            color: var(--text); 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            margin: 0; 
        }
        .container { 
            background: var(--card); 
            padding: 30px; 
            border-radius: 12px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.5); 
            text-align: center; 
            width: 90%; 
            max-width: 500px; 
        }
        h1 { 
            font-size: 24px; 
            margin-bottom: 20px; 
            color: var(--primary); 
        }
        input[type="text"] { 
            width: 100%; 
            padding: 12px; 
            border-radius: 8px; 
            border: 1px solid #333; 
            background: #2a2a2a; 
            color: #fff; 
            box-sizing: border-box; 
            margin-bottom: 15px; 
            font-size: 14px; 
        }
        button { 
            background: var(--primary); 
            color: white; 
            border: none; 
            padding: 12px 20px; 
            border-radius: 8px; 
            font-size: 16px; 
            font-weight: bold; 
            cursor: pointer; 
            width: 100%; 
            transition: background 0.2s; 
        }
        button:hover { 
            background: #2563eb; 
        }
        .footer { 
            margin-top: 20px; 
            font-size: 12px; 
            color: #888; 
            font-style: italic; 
        }
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

@app.route('/descargar')
def descargar():
    video_url = request.args.get('url')
    if not video_url:
        return "Por favor, introduce una URL válida.", 400

    opciones = {
        'quiet': True,
        'no_warnings': True,
        # Esto le dice a yt-dlp: dame el mejor MP4 con audio incluido,
        # o si no existe, el mejor formato disponible en un solo archivo.
        'format': 'best[ext=mp4]/best',
    }

    if os.path.exists('cookies.txt'):
        opciones['cookiefile'] = 'cookies.txt'

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(video_url, download=False)

        # yt-dlp ya eligió el mejor formato compatible
        url_directa = info.get('url')
        titulo = info.get('title', 'video').replace('/', '-')
        ext = info.get('ext', 'mp4')

        if not url_directa:
            return "No se encontró URL de descarga.", 500

        # Headers que YouTube espera para servir el archivo
        headers_yt = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.youtube.com/',
        }

        # Hacemos streaming del video a través de tu servidor
        r = req_lib.get(url_directa, headers=headers_yt, stream=True, timeout=30)

        def generar():
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    yield chunk

        return Response(
            generar(),
            content_type=r.headers.get('Content-Type', f'video/{ext}'),
            headers={
                'Content-Disposition': f'attachment; filename="{titulo}.{ext}"',
                'Content-Length': r.headers.get('Content-Length', ''),
            }
        )

    except Exception as e:
        return f"Error al procesar el video: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
