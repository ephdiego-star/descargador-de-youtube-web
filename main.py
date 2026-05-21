import os
import glob
import yt_dlp
from flask import Flask, render_template_string, request, Response

app = Flask(__name__)
COOKIES_PATH = 'cookies.txt'

# ... (Mantén el resto de PAGINA_HTML igual) ...

@app.route('/descargar')
def descargar():
    video_url = request.args.get('url')
    if not video_url:
        return "URL no válida", 400

    # CAMBIO CRÍTICO: 'best' obliga a bajar el formato que ya tiene audio y video unidos.
    # Esto elimina la dependencia de ffmpeg y el error de "Requested format is not available"
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

        archivos = glob.glob(f'/tmp/{video_id}.*')
        if not archivos:
            return "No se pudo obtener el archivo.", 500

        archivo = archivos[0]
        ext = archivo.split('.')[-1]

        def generar():
            with open(archivo, 'rb') as f:
                while chunk := f.read(1024 * 256):
                    yield chunk
            if os.path.exists(archivo):
                os.remove(archivo)

        return Response(
            generar(),
            content_type=f'video/{ext}',
            headers={'Content-Disposition': f'attachment; filename="{titulo}.{ext}"'}
        )

    except Exception as e:
        return f"Error técnico: {str(e)}", 500

# ... (El resto del código igual) ...
