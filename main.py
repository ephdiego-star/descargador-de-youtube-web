import os
import glob
import tempfile
from flask import Flask, request, send_file, render_template_string
import yt_dlp
import imageio_ffmpeg

app = Flask(__name__)

def obtener_ruta_cookies():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ruta_cookies = os.path.join(base_dir, 'cookies.txt')
    if os.path.exists(ruta_cookies):
        return ruta_cookies
    return None

@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Media Downloader</title>
        <style>
            body {
                background-color: #121212;
                color: #e0e0e0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .card {
                background-color: #1e1e1e;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.6);
                width: 100%;
                max-width: 480px;
                border: 1px solid #2d2d2d;
            }
            h2 {
                color: #ffffff;
                text-align: center;
                margin-top: 0;
                margin-bottom: 30px;
                font-size: 24px;
                letter-spacing: 0.5px;
            }
            label {
                display: block;
                margin-bottom: 9px;
                color: #b3b3b3;
                font-size: 14px;
            }
            input[type="text"], select {
                width: 100%;
                padding: 12px 16px;
                margin-bottom: 24px;
                border: 1px solid #333333;
                border-radius: 6px;
                background-color: #252525;
                color: #ffffff;
                font-size: 15px;
                box-sizing: border-box;
                transition: border-color 0.3s ease;
            }
            input[type="text"]:focus, select:focus {
                border-color: #007bff;
                outline: none;
            }
            button {
                width: 100%;
                padding: 14px;
                background-color: #007bff;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: background-color 0.2s ease;
                box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
            }
            button:hover {
                background-color: #0056b3;
            }
            .footer-text {
                text-align: center;
                font-size: 11px;
                color: #666666;
                margin-top: 20px;
                line-height: 1.4;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Media Downloader</h2>
            <form action="/descargar" method="POST">
                <label>Enlace del video de YouTube</label>
                <input type="text" name="url" placeholder="https://www.youtube.com/watch?v=..." required>
                
                <label>Tipo de formato</label>
                <select name="formato" id="formato">
                    <option value="video">Video (MP4 estándar)</option>
                    <option value="audio">Audio MP3 (Solo Música)</option>
                </select>
                
                <label>Calidad preferida (Solo para Video)</label>
                <select name="calidad" id="calidad">
                    <option value="1080p">1080p (Alta Definición)</option>
                    <option value="720p" selected>720p (Estándar HD)</option>
                    <option value="480p">480p (Calidad Media)</option>
                    <option value="360p">360p (Calidad Baja)</option>
                </select>
                
                <button type="submit">Descargar ahora</button>
            </form>
            <div class="footer-text">
                Modo portable universal activado. Los binarios de procesamiento se autogestionan a través del entorno virtual.
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/descargar', methods=['POST'])
def descargar():
    url = request.form.get('url')
    formato = request.form.get('formato', 'video')
    calidad = request.form.get('calidad', '720p')

    if not url:
        return "Error: No se especificó ninguna URL.", 400

    dir_temporal = tempfile.gettempdir()
    ruta_ffmpeg_automatica = imageio_ffmpeg.get_ffmpeg_exe()

    opciones = {
        'quiet': True,
        'no_warnings': True,
        'outtmpl': os.path.join(dir_temporal, '%(id)s.%(ext)s'),
        'socket_timeout': 30,
        'retries': 10,
        'fragment_retries': 10,
        'extractor_retries': 5,
        'ignoreerrors': False,
        'ffmpeg_location': ruta_ffmpeg_automatica,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
    }

    ruta_cookies = obtener_ruta_cookies()
    if ruta_cookies:
        opciones['cookiefile'] = ruta_cookies

    if formato == 'audio':
        formatos_a_probar = ['bestaudio/best']
        opciones['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        opciones['merge_output_format'] = 'mp4'
        if calidad == '1080p':
            formatos_a_probar = ['bestvideo[height<=1080]+bestaudio/best']
        elif calidad == '720p':
            formatos_a_probar = ['bestvideo[height<=720]+bestaudio/best']
        elif calidad == '480p':
            formatos_a_probar = ['bestvideo[height<=480]+bestaudio/best']
        elif calidad == '360p':
            formatos_a_probar = ['bestvideo[height<=360]+bestaudio/best']
        else:
            formatos_a_probar = ['bestvideo+bestaudio/best']

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            id_video = info_dict.get('id', 'video')
            titulo_video = info_dict.get('title', 'descarga')
            
            ydl.params['format'] = formatos_a_probar[0]
            ydl.download([url])

        patron_busqueda = os.path.join(dir_temporal, f"{id_video}.*")
        archivos_encontrados = glob.glob(patron_busqueda)
        
        if not archivos_encontrados:
            return "Error: El archivo procesado no se localizó en la ruta temporal.", 500
            
        ruta_archivo_real = archivos_encontrados[0]
        _, extension_real = os.path.splitext(ruta_archivo_real)

        if formato == 'audio':
            mimetype_final = 'audio/mpeg'
            extension_final = '.mp3'
        else:
            mimetype_final = 'video/mp4'
            extension_final = '.mp4'

        caracteres_limpios = "".join([c for c in titulo_video if c.isalpha() or c.isdigit() or c in ' -_']).strip()
        nombre_descarga = f"{caracteres_limpios}{extension_final}"

        return send_file(
            ruta_archivo_real,
            mimetype=mimetype_final,
            as_attachment=True,
            download_name=nombre_descarga
        )

    except Exception as e:
        return f"Error: No se pudo procesar la descarga de YouTube. Detalle: {str(e)}", 500

if __name__ == '__main__':
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=puerto)
