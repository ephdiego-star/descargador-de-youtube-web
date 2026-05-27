import os

import glob

import yt_dlp

import traceback

import sys

import logging

from flask import Flask, render_template_string, request, Response



app = Flask(_name_)



# Configurar logging

logging.basicConfig(

    level=logging.INFO,

    format='%(asctime)s - %(levelname)s - %(message)s',

    stream=sys.stdout

)

logger = logging.getLogger(_name_)



COOKIES_PATH = '/tmp/cookies.txt'



PAGINA_HTML = """

<!DOCTYPE html>

<html lang="es">

<head>

    <meta charset="UTF-8">

    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>YouTube Downloader</title>

    <style>

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {

            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;

            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

            min-height: 100vh;

            display: flex;

            justify-content: center;

            align-items: center;

            padding: 20px;

        }

        .container {

            background: rgba(255, 255, 255, 0.95);

            border-radius: 24px;

            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);

            padding: 30px;

            max-width: 500px;

            width: 100%;

        }

        h1 { color: #1a1a1a; font-size: 26px; font-weight: 700; margin-bottom: 8px; text-align: center; }

        .subtitle { color: #666; text-align: center; margin-bottom: 25px; font-size: 13px; }

        input[type="text"] {

            width: 100%; padding: 14px; border: 2px solid #e0e0e0;

            border-radius: 10px; font-size: 14px; margin-bottom: 12px;

            background: #f8f9fa; outline: none;

        }

        input[type="text"]:focus { border-color: #667eea; background: white; }

        

        .section-title {

            font-size: 13px;

            font-weight: 600;

            color: #333;

            margin-bottom: 8px;

            text-align: center;

        }

        

        .format-selector, .quality-selector { 

            display: flex; 

            gap: 8px; 

            margin-bottom: 12px;

            flex-wrap: wrap;

            justify-content: center;

        }

        .format-btn, .quality-btn {

            padding: 10px 14px; 

            border: 2px solid #667eea;

            background: white; 

            color: #667eea; 

            border-radius: 8px;

            cursor: pointer; 

            font-size: 13px;

            transition: all 0.3s;

        }

        .format-btn.active, .quality-btn.active { 

            background: #667eea; 

            color: white; 

        }

        .format-btn:hover, .quality-btn:hover {

            background: #667eea;

            color: white;

        }

        button[type="submit"] {

            width: 100%; 

            padding: 14px;

            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

            color: white; 

            border: none; 

            border-radius: 10px;

            font-size: 15px; 

            font-weight: 600; 

            cursor: pointer; 

            margin-top: 5px;

            transition: transform 0.2s;

        }

        button[type="submit"]:hover { transform: translateY(-2px); }

        .error-message {

            display: none; 

            background: #fee; 

            color: #c33;

            padding: 10px; 

            border-radius: 8px; 

            margin-top: 12px;

            text-align: center; 

            font-size: 13px;

        }

        .error-message.show { display: block; }

        .loading {

            display: none; 

            text-align: center; 

            margin-top: 15px;

        }

        .loading.show { display: block; }

        .spinner {

            border: 3px solid #e0e0e0; 

            border-top: 3px solid #667eea;

            border-radius: 50%; 

            width: 35px; 

            height: 35px;

            animation: spin 1s linear infinite; 

            margin: 0 auto 8px;

        }

        @keyframes spin {

            0% { transform: rotate(0deg); }

            100% { transform: rotate(360deg); }

        }

        .quality-selector.hidden { display: none; }

    </style>

</head>

<body>

    <div class="container">

        <h1>🎬 YouTube Downloader</h1>

        <p class="subtitle">Descarga videos en MP4 compatible</p>

        

        <form id="downloadForm" method="GET" action="/descargar">

            <input type="text" id="urlInput" name="url" 

                   placeholder="Pega el enlace de YouTube aquí..." required>

            

            <p class="section-title">📁 Formato:</p>

            <div class="format-selector">

                <button type="button" id="videoBtn" class="format-btn active" 

                        onclick="selectFormat('video')">🎬 Video</button>

                <button type="button" id="audioBtn" class="format-btn" 

                        onclick="selectFormat('audio')">🎵 Audio MP3</button>

            </div>

            

            <p class="section-title">📺 Calidad:</p>

            <div class="quality-selector" id="qualitySelector">

                <button type="button" id="q1080" class="quality-btn" 

                        onclick="selectQuality('1080p')">1080p</button>

                <button type="button" id="q720" class="quality-btn active" 

                        onclick="selectQuality('720p')">720p</button>

                <button type="button" id="q480" class="quality-btn" 

                        onclick="selectQuality('480p')">480p</button>

                <button type="button" id="q360" class="quality-btn" 

                        onclick="selectQuality('360p')">360p</button>

                <button type="button" id="qbest" class="quality-btn" 

                        onclick="selectQuality('best')">✨ Mejor</button>

            </div>

            

            <input type="hidden" id="formatInput" name="format" value="video">

            <input type="hidden" id="qualityInput" name="quality" value="720p">

            

            <button type="submit" id="downloadBtn">⬇️ Descargar Video 720p</button>

        </form>

        

        <div class="loading" id="loading">

            <div class="spinner"></div>

            <p>⏳ Descargando, por favor espera...</p>

        </div>

        

        <div class="error-message" id="errorMessage"></div>

    </div>



    <script>

        var currentFormat = 'video';

        var currentQuality = '720p';

        

        function selectFormat(format) {

            currentFormat = format;

            document.getElementById('formatInput').value = format;

            

            document.getElementById('videoBtn').classList.remove('active');

            document.getElementById('audioBtn').classList.remove('active');

            

            if (format === 'video') {

                document.getElementById('videoBtn').classList.add('active');

                document.getElementById('qualitySelector').classList.remove('hidden');

                updateButtonText();

            } else {

                document.getElementById('audioBtn').classList.add('active');

                document.getElementById('qualitySelector').classList.add('hidden');

                document.getElementById('downloadBtn').textContent = '🎵 Descargar Audio MP3';

            }

        }

        

        function selectQuality(quality) {

            currentQuality = quality;

            document.getElementById('qualityInput').value = quality;

            

            document.querySelectorAll('.quality-btn').forEach(function(btn) {

                btn.classList.remove('active');

            });

            

            var btnId = 'q' + quality.replace('p', '');

            if (quality === 'best') btnId = 'qbest';

            var activeBtn = document.getElementById(btnId);

            if (activeBtn) activeBtn.classList.add('active');

            

            updateButtonText();

        }

        

        function updateButtonText() {

            var qualityNames = {

                '1080p': '1080p Full HD',

                '720p': '720p HD',

                '480p': '480p SD',

                '360p': '360p',

                'best': 'Mejor Calidad'

            };

            document.getElementById('downloadBtn').textContent = 

                '⬇️ Descargar Video ' + qualityNames[currentQuality];

        }

        

        document.getElementById('downloadForm').addEventListener('submit', function(e) {

            var url = document.getElementById('urlInput').value.trim();

            var errorDiv = document.getElementById('errorMessage');

            

            errorDiv.classList.remove('show');

            

            if (!url) {

                e.preventDefault();

                errorDiv.textContent = '❌ Ingresa un enlace de YouTube';

                errorDiv.classList.add('show');

                return false;

            }

            

            if (url.indexOf('youtube.com') === -1 && url.indexOf('youtu.be') === -1) {

                e.preventDefault();

                errorDiv.textContent = '❌ Enlace no válido';

                errorDiv.classList.add('show');

                return false;

            }

            

            document.getElementById('loading').classList.add('show');

            document.getElementById('downloadBtn').textContent = '⏳ Procesando...';

            document.getElementById('downloadBtn').style.opacity = '0.6';

            

            return true;

        });

    </script>

</body>

</html>

"""



def cargar_cookies():

    """Carga las cookies desde variable de entorno"""

    try:

        cookies_env = os.environ.get('YOUTUBE_COOKIES')

        if cookies_env:

            with open(COOKIES_PATH, 'w', encoding='utf-8') as f:

                f.write(cookies_env)

            return True

        return False

    except Exception as e:

        logger.error(f"Error cookies: {e}")

        return False



@app.route('/')

def inicio():

    return render_template_string(PAGINA_HTML)



@app.route('/descargar', methods=['GET'])

def descargar():

    try:

        video_url = request.args.get('url')

        formato = request.args.get('format', 'video')

        calidad = request.args.get('quality', '720p')

        

        logger.info(f"Descargando: {video_url} - {formato} - {calidad}")

        

        if not video_url:

            return "Error: URL no proporcionada", 400



        if 'youtube.com' not in video_url and 'youtu.be' not in video_url:

            return "Error: URL no válida", 400



        cargar_cookies()



        # Configuración ultra compatible

        opciones = {

            'quiet': True,

            'no_warnings': True,

            'outtmpl': '/tmp/%(id)s.%(ext)s',

            'socket_timeout': 30,

            'retries': 10,

            'fragment_retries': 10,

            'extractor_retries': 5,

            'ignoreerrors': True,  # Ignorar errores de formato

            'http_headers': {

                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',

            },

        }



        if formato == 'audio':

            opciones['format'] = 'bestaudio/best'

            opciones['postprocessors'] = [{

                'key': 'FFmpegExtractAudio',

                'preferredcodec': 'mp3',

                'preferredquality': '192',

            }]

        else:

            # Lista de formatos a probar, del más específico al más genérico

            if calidad == '1080p':

                formatos_a_probar = [

                    'best[height<=1080]',

                    'best[height<=720]',

                    'best[height<=480]',

                    'best',

                    'worst',

                ]

            elif calidad == '720p':

                formatos_a_probar = [

                    'best[height<=720]',

                    'best[height<=480]',

                    'best[height<=360]',

                    'best',

                    'worst',

                ]

            elif calidad == '480p':

                formatos_a_probar = [

                    'best[height<=480]',

                    'best[height<=360]',

                    'best',

                    'worst',

                ]

            elif calidad == '360p':

                formatos_a_probar = [

                    'best[height<=360]',

                    'best',

                    'worst',

                ]

            else:  # 'best'

                formatos_a_probar = [

                    'best',

                    'worst',

                ]

            

            opciones['format'] = '/'.join(formatos_a_probar)



        if os.path.exists(COOKIES_PATH):

            opciones['cookiefile'] = COOKIES_PATH



        # Intentar descargar con cada formato

        info = None

        ultimo_error = None

        

        for intento, formato_str in enumerate(formatos_a_probar if formato == 'video' else ['bestaudio/best']):

            try:

                opciones_intento = opciones.copy()

                opciones_intento['format'] = formato_str

                logger.info(f"Intento {intento + 1}: {formato_str}")

                

                with yt_dlp.YoutubeDL(opciones_intento) as ydl:

                    info = ydl.extract_info(video_url, download=True)

                    logger.info(f"¡Éxito con formato: {formato_str}!")

                    break

                    

            except Exception as e:

                ultimo_error = str(e)

                logger.warning(f"Falló formato {formato_str}: {ultimo_error}")

                continue

        

        if not info:

            return f"Error: No se pudo descargar. Último error: {ultimo_error}", 500



        video_id = info.get('id')

        titulo = info.get('title', 'video')

        titulo = "".join(c for c in titulo if c.isalnum() or c in (' ', '-', '_')).rstrip()

        

        altura = info.get('height', '?')

        logger.info(f"Descargado: {titulo} ({altura}p)")



        # Buscar archivo

        archivos = glob.glob(f'/tmp/{video_id}.*')

        

        if not archivos:

            return "Error: No se encontró el archivo descargado", 500



        # Elegir mejor archivo

        if formato == 'audio':

            preferidos = [f for f in archivos if f.endswith('.mp3')]

        else:

            preferidos = [f for f in archivos if f.endswith('.mp4')]

        

        archivo = preferidos[0] if preferidos else archivos[0]

        ext = archivo.split('.')[-1]

        tamaño = os.path.getsize(archivo)



        def generar():

            try:

                with open(archivo, 'rb') as f:

                    while True:

                        chunk = f.read(8192)

                        if not chunk:

                            break

                        yield chunk

            finally:

                try:

                    os.remove(archivo)

                    for f in glob.glob(f'/tmp/{video_id}*'):

                        if os.path.exists(f):

                            os.remove(f)

                except:

                    pass



        return Response(

            generar(),

            mimetype='video/mp4' if ext == 'mp4' else 'audio/mpeg',

            headers={

                'Content-Disposition': f'attachment; filename="{titulo}.{ext}"',

            }

        )



    except Exception as e:

        logger.error(f"Error final: {traceback.format_exc()}")

        return f"Error: {str(e)}", 500



@app.route('/health')

def health():

    return {'status': 'ok'}



if _name_ == '_main_':

    port = int(os.environ.get('PORT', 8080))

    app.run(host='0.0.0.0', port=port)
