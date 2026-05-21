import os
import glob
import yt_dlp
import shutil
from flask import Flask, render_template_string, request, Response

app = Flask(__name__)

# Definimos las cookies en la raíz donde las subiste a GitHub
COOKIES_SOURCE = 'cookies.txt'
COOKIES_DEST = '/tmp/cookies.txt'

# Copiamos las cookies a /tmp al arrancar el servidor
if os.path.exists(COOKIES_SOURCE):
    shutil.copy(COOKIES_SOURCE, COOKIES_DEST)

PAGINA_HTML = """
<!DOCTYPE html>
<html lang="es">
<body>
    <h1>Descargador</h1>
    <form action="/descargar" method="GET">
        <input type="text" name="url" placeholder="Pega el link aquí" required>
        <button type="submit">Descargar</button>
    </form>
</body>
</html>
"""

@app.route('/')
def inicio():
    return render_template_string(PAGINA_HTML)

@app.route('/descargar', methods=['GET'])
def descargar():
    video_url = request.args.get('url')
    if not video_url:
        return "No se recibió ninguna URL.", 400

    # Usamos ffmpeg (asegúrate de tener el nixpacks.toml con ffmpeg)
    opciones = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': '/tmp/%(id)s.%(ext)s',
        'cookiefile': COOKIES_DEST if os.path.exists(COOKIES_DEST) else None,
    }

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_id = info.get('id')
            titulo = info.get('title', 'video').replace('/', '-')

        archivos = glob.glob(f'/tmp/{video_id}.*')
        if not archivos:
            return "No se pudo encontrar el archivo descargado.", 500

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
            mimetype='video/mp4',
            headers={'Content-Disposition': f'attachment; filename="{titulo}.mp4"'}
        )
    except Exception as e:
        return f"Error técnico: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
