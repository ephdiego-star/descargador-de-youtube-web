import os
import glob
import yt_dlp
from flask import Flask, render_template_string, request, Response

app = Flask(__name__)

# Usamos la ruta local donde Railway clona el repo
COOKIES_PATH = 'cookies.txt'

PAGINA_HTML = """
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>Descargador</title></head>
<body>
    <h1>Descargador Web</h1>
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
    if not video_url: return "No URL", 400

    # CAMBIO RADICAL: 'format': 'best[ext=mp4]' 
    # Esto fuerza a bajar solo archivos que ya son MP4 y tienen audio+video juntos.
    # No necesita ffmpeg y nunca dará el error de formato no disponible.
    opciones = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best[ext=mp4]/best', 
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
        if not archivos: return "Error: No se descargó nada.", 500

        archivo = archivos[0]
        def generar():
            with open(archivo, 'rb') as f:
                while chunk := f.read(1024 * 256): yield chunk
            if os.path.exists(archivo): os.remove(archivo)

        return Response(generar(), mimetype='video/mp4', 
                        headers={'Content-Disposition': f'attachment; filename="{titulo}.mp4"'})
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
