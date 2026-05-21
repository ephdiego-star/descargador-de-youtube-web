import os
import glob
import yt_dlp
from flask import Flask, render_template_string, request, Response

app = Flask(__name__)
COOKIES_PATH = 'cookies.txt'

# ... [El resto del HTML igual] ...

@app.route('/descargar', methods=['GET'])
def descargar():
    video_url = request.args.get('url')
    if not video_url:
        return "No se recibió ninguna URL.", 400

    # Esta configuración es la estándar de oro para servidores sin entorno gráfico
    opciones = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bestvideo+bestaudio/best', # Busca el mejor video + mejor audio
        'merge_output_format': 'mp4',        # Une ambos en un MP4 final
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
            return "El video se descargó pero no se pudo unir (falta ffmpeg).", 500

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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
