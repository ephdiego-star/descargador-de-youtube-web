import os
import glob
import tempfile
from flask import Flask, request, send_file, render_template_string
import yt_dlp

app = Flask(__name__)

def obtener_ruta_cookies():
    # Busca el archivo cookies.txt en la misma carpeta que main.py
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ruta_cookies = os.path.join(base_dir, 'cookies.txt')
    if os.path.exists(ruta_cookies):
        return ruta_cookies
    return None

@app.route('/')
def index():
    # Formulario HTML simple integrado para realizar las pruebas directamente
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Descargador de YouTube Portátil</title>
        <style>
            body { font-family: sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; }
            input, select, button { width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; }
            button { background-color: #007bff; color: white; border: none; cursor: pointer; }
            button:hover { background-color: #0056b3; }
        </style>
    </head>
    <body>
        <h2>Descargador de YouTube (Sin dependencias de sistema)</h2>
        <form action="/descargar" method="POST">
            <label>Enlace del video:</label>
            <input type="text" name="url" placeholder="https://www.youtube.com/watch?v=..." required>
            
            <label>Tipo de descarga:</label>
            <select name="formato">
                <option value="video">Video (Máximo 720p - Formato nativo)</option>
                <option value="audio">Audio (Formato nativo sin conversión)</option>
            </select>
            
            <button type="submit">Procesar Descarga</button>
        </form>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/descargar', methods=['POST'])
def descargar():
    url = request.form.get('url')
    formato = request.form.get('formato', 'video')

    if not url:
        return "Error: No proporcionaste una URL válida.", 400

    # Obtiene la carpeta temporal del sistema (funciona en cualquier PC o servidor)
    dir_temporal = tempfile.gettempdir()

    # Opciones configuradas para evitar el uso de FFmpeg
    opciones = {
        'quiet': True,
        'no_warnings': True,
        'outtmpl': os.path.join(dir_temporal, '%(id)s.%(ext)s'),
        'socket_timeout': 30,
        'retries': 10,
        'fragment_retries': 10,
        'extractor_retries': 5,
        'ignoreerrors': False,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
    }

    ruta_cookies = obtener_ruta_cookies()
    if ruta_cookies:
        opciones['cookiefile'] = ruta_cookies

    # Selección de flujos progresivos completos de YouTube
    if formato == 'audio':
        formatos_a_probar = ['bestaudio/best']
    else:
        formatos_a_probar = ['best[ext=mp4]/best']

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            # Extrae metadatos esenciales antes de la descarga
            info_dict = ydl.extract_info(url, download=False)
            id_video = info_dict.get('id', 'video')
            titulo_video = info_dict.get('title', 'descarga')
            
            # Asigna el formato definitivo y ejecuta
            ydl.params['format'] = formatos_a_probar[0]
            ydl.download([url])

        # Localiza de forma dinámica el archivo usando glob para detectar la extensión real
        patron_busqueda = os.path.join(dir_temporal, f"{id_video}.*")
        archivos_encontrados = glob.glob(patron_busqueda)
        
        if not archivos_encontrados:
            return "Error: El archivo descargado no pudo ser localizado en el directorio temporal.", 500
            
        ruta_archivo_real = archivos_encontrados[0]
        _, extension_real = os.path.splitext(ruta_archivo_real)

        # Mapea las cabeceras MIME correctas según lo que entregó el servidor de Google
        if formato == 'audio':
            if extension_real == '.m4a':
                mimetype_final = 'audio/mp4'
            elif extension_real == '.webm':
                mimetype_final = 'audio/webm'
            else:
                mimetype_final = 'audio/mpeg'
        else:
            if extension_real == '.webm':
                mimetype_final = 'video/webm'
            else:
                mimetype_final = 'video/mp4'

        # Limpia el título quitando caracteres extraños para el nombre final del archivo
        caracteres_limpios = "".join([c for c in titulo_video if c.isalpha() or c.isdigit() or c in ' -_']).strip()
        nombre_descarga = f"{caracteres_limpios}{extension_real}"

        return send_file(
            ruta_archivo_real,
            mimetype=mimetype_final,
            as_attachment=True,
            download_name=nombre_descarga
        )

    except Exception as e:
        return f"Error: No se pudo procesar la descarga de YouTube. Detalle: {str(e)}", 500

if __name__ == '__main__':
    # Lee el puerto asignado por la plataforma en la nube o usa el 5000 por defecto de forma local
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=puerto)
