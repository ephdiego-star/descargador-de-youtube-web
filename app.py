import os
import yt_dlp
from flask import Flask, render_template_string, request, Response
import requests as req_lib

app = Flask(__name__)

PAGINA_HTML = """..."""  # (tu HTML sin cambios)

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
