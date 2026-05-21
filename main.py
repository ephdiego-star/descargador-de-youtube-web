import os
import glob
import yt_dlp
from flask import Flask, render_template_string, request, Response

app = Flask(__name__)
COOKIES_PATH = 'cookies.txt'

PAGINA_HTML = """
<!DOCTYPE html>
<html lang="es">
<body>
    <h1>Descargador</h1>
    <form action="/descargar" method="GET">
        <input type="text" name="url" placeholder="Pega el link aquí" required style="width: 300px;">
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

    # CAMBIO RADICAL: Eliminamos la restricción de 'best'. 
    # Dejamos que yt-dlp elija automáticamente basándose en lo que YouTube entregue.
    opciones = {
        'quiet': True,
        'no_warnings': True,
        'outtmpl': '/tmp/%(id)s.%(ext)s',
    }

    if os.path.exists(COOKIES_PATH):
        opciones['cookiefile'] = COOKIES_PATH

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            # Extraemos info primero para ver qué hay disponible
            info = ydl.extract_info(video_url, download=True)
            video_id = info.get('id')
            titulo = info.get('title', 'video').replace('/', '-')

        # Buscamos lo que sea que haya bajado (mp4, mkv, webm, etc)
        archivos = glob.glob(f'/tmp/{video_id}.*')
        if not archivos:
            return "No se encontró el archivo descargado.", 500

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
            mimetype=f'video/{ext}',
            headers={'Content-Disposition': f'attachment; filename="{titulo}.{ext}"'}
        )

    except Exception as e:
        return f"Error técnico: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
