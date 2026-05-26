import os
import glob
import yt_dlp
import traceback
import sys
import logging
import urllib.parse
from flask import Flask, render_template_string, request, Response

app = Flask(_name_)

# Configuración de registro del sistema
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(_name_)

# Rutas de entorno de ejecución
COOKIES_PATH = './temp/cookies.txt'

PAGINA_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Universal Downloader</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #2b2b2b 0%, #1a1a1a 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
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
        input[type="text"]:focus { border-color: #d32f2f; background: white; }
        
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
            border: 2px solid #333;
            background: white; 
            color: #333; 
            border-radius: 8px;
            cursor: pointer; 
            font-size: 13px;
            transition: all 0.3s;
        }
        .format-btn.active, .quality-btn.active { 
            background: #d32f2f; 
            border-color: #d32f2f;
            color: white; 
        }
        .format-btn:hover, .quality-btn:hover {
            background: #d32f2f;
            border-color: #d32f2f;
            color: white;
        }
        button[type="submit"] {
            width: 100%; 
            padding: 14px;
            background: linear-gradient(135deg, #d32f2f 0%, #9a0007 100%);
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
            font-weight: bold;
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
            border-top: 3px solid #d32f2f;
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
        .platform-icons { text-align: center; font-size: 20px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ Universal Downloader</h1>
        <div class="platform-icons">📱 🐦 📸 🎵 🎬</div>
        <p class="subtitle">Descarga desde YouTube, X, Instagram, Facebook y TikTok</p>
        
        <form id="downloadForm" method="GET" action="/descargar">
            <input type="text" id="urlInput" name="url" 
                   placeholder="Pega el enlace aquí..." required>
            
            <p class="section-title">📁 Formato:</p>
            <div class="format-selector">
                <button type="button" id="videoBtn" class="format-btn active" 
                        onclick="selectFormat('video')">🎬 Video</button>
                <button type="button" id="audioBtn" class="format-btn" 
                        onclick="selectFormat('audio')">🎵 Audio MP3</button>
                <button type="button" id="imagenBtn" class="format-btn" 
                        onclick="selectFormat('imagen')">📸 Imagen</button>
            </div>
            
            <p class="section-title">📺 Calidad (Solo YouTube):</p>
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
            
            <button type="submit" id="downloadBtn">⬇️ Descargar Archivo</button>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>⏳ Extrayendo datos, aguanta un momento...</p>
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
            document.getElementById('imagenBtn').classList.remove('active');
            
            if (format === 'video') {
                document.getElementById('videoBtn').classList.add('active');
                document.getElementById('qualitySelector').classList.remove('hidden');
                updateButtonText();
            } else if (format === 'audio') {
                document.getElementById('audioBtn').classList.add('active');
                document.getElementById('qualitySelector').classList.add('hidden');
                document.getElementById('downloadBtn').textContent = '🎵 Descargar Audio MP3';
            } else {
                document.getElementById('imagenBtn').classList.add('active');
                document.getElementById('qualitySelector').classList.add('hidden');
                document.getElementById('downloadBtn').textContent = '📸 Descargar Imagen';
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
                errorDiv.textContent = '❌ Ingresa un enlace válido';
                errorDiv.classList.add('show');
                return false;
            }
            
            var urlLower = url.toLowerCase();
            var dominiosValidos = ['youtube.com', 'youtu.be', 'twitter.com', 'x.com', 'instagram.com', 'facebook.com', 'tiktok.com', 'pinterest.com'];
            var esValido = dominiosValidos.some(function(dominio) {
                return urlLower.indexOf(dominio) !== -1;
            });

            if (!esValido) {
                e.preventDefault();
                errorDiv.textContent = '❌ Plataforma no soportada.';
                errorDiv.classList.add('show');
                return false;
            }
            
            document.getElementById('loading').classList.add('show');
            document.getElementById('downloadBtn').textContent = '⏳ Procesando en el servidor...';
            document.getElementById('downloadBtn').style.opacity = '0.6';
            
            return true;
        });
    </script>
</body>
</html>
"""

def cargar_cookies():
    """Carga las variables de sesión para autenticación"""
    try:
        cookies_env = os.environ.get('YOUTUBE_COOKIES')
        if cookies_env:
            with open(COOKIES_PATH, 'w', encoding='utf-8') as f:
                f.write(cookies_env)
            return True
        return False
    except Exception as e:
        logger.error(f"Error en el manejo de cookies: {e}")
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
        
        logger.info(f"Solicitud: {video_url} | Formato: {formato} | Calidad: {calidad}")
        
        if not video_url:
            return "Error: URL no proporcionada", 400

        dominios_permitidos = ['youtube.com', 'youtu.be', 'twitter.com', 'x.com', 'instagram.com', 'facebook.com', 'tiktok.com', 'pinterest.com']
        if not any(dominio in video_url.lower() for dominio in dominios_permitidos):
            return "Error: La plataforma solicitada no es soportada por el servidor actual.", 400

        cargar_cookies()

        # Configuración principal
        opciones = {
            'quiet': True,
            'no_warnings': True,
            'outtmpl': './temp/%(id)s.%(ext)s',
            'socket_timeout': 30,
            'retries': 10,
            'fragment_retries': 10,
            'extractor_retries': 5,
            'ignoreerrors': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
        }

        # Aplicación de rutas según la intención del formato
        if formato == 'audio':
            opciones['format'] = 'bestaudio/best'
            opciones['ffmpeg_location'] = r'C:\ffmpeg\bin'
            opciones['writethumbnail'] = True
            opciones['postprocessors'] = [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                },
                {
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                },
                {
                    'key': 'EmbedThumbnail',
                    'already_have_thumbnail': False,
                }
            ]
            formatos_a_probar = ['bestaudio/best']

        elif formato == 'imagen':
            # Evita procesamientos de FFmpeg para forzar descarga estática
            opciones['format'] = 'best'
            formatos_a_probar = ['best']

        else:
            opciones['merge_output_format'] = 'mp4'
            opciones['ffmpeg_location'] = r'C:\ffmpeg\bin'
            es_youtube = 'youtube.com' in video_url.lower() or 'youtu.be' in video_url.lower()
            
            if es_youtube:
                if calidad == '1080p':
                    formatos_a_probar = ['bestvideo[height<=1080]+bestaudio/best', 'best']
                elif calidad == '720p':
                    formatos_a_probar = ['bestvideo[height<=720]+bestaudio/best', 'best']
                elif calidad == '480p':
                    formatos_a_probar = ['bestvideo[height<=480]+bestaudio/best', 'best']
                elif calidad == '360p':
                    formatos_a_probar = ['bestvideo[height<=360]+bestaudio/best', 'best']
                else:  
                    formatos_a_probar = ['bestvideo+bestaudio/best', 'best']
            else:
                formatos_a_probar = ['bestvideo+bestaudio/best', 'best', 'worst']
            
            opciones['format'] = '/'.join(formatos_a_probar)

        if os.path.exists(COOKIES_PATH):
            opciones['cookiefile'] = COOKIES_PATH

        # Extracción
        info = None
        ultimo_error = None
        
        for intento, formato_str in enumerate(formatos_a_probar):
            try:
                opciones_intento = opciones.copy()
                opciones_intento['format'] = formato_str
                with yt_dlp.YoutubeDL(opciones_intento) as ydl:
                    info = ydl.extract_info(video_url, download=True)
                    break
            except Exception as e:
                ultimo_error = str(e)
                continue
        
        if not info:
            return f"Error en el servidor: Detalle técnico: {ultimo_error}", 500

        video_id = info.get('id', 'archivo')
        titulo = info.get('title', 'descarga')
        titulo = "".join(c for c in titulo if c.isalnum() or c in (' ', '-', '_')).rstrip()

        archivos = glob.glob(f'./temp/{video_id}.*')
        
        if not archivos:
            return "Error de I/O: El archivo no se localizó en el directorio temporal.", 500

        # Selección estricta del contenedor basado en la extensión
        if formato == 'audio':
            preferidos = [f for f in archivos if f.lower().endswith('.mp3')]
        elif formato == 'imagen':
            preferidos = [f for f in archivos if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
        else:
            preferidos = [f for f in archivos if f.lower().endswith('.mp4')]
        
        archivo = preferidos[0] if preferidos else archivos[0]
        ext = archivo.split('.')[-1].lower()

        # Enrutamiento de Mimetypes para evitar que las fotos se corrompan o no carguen
        if ext in ['jpg', 'jpeg']:
            mimetype_salida = 'image/jpeg'
        elif ext == 'png':
            mimetype_salida = 'image/png'
        elif ext == 'webp':
            mimetype_salida = 'image/webp'
        elif ext == 'mp3':
            mimetype_salida = 'audio/mpeg'
        else:
            mimetype_salida = 'video/mp4'

        def generar_flujo_datos():
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
                    for f in glob.glob(f'./temp/{video_id}*'):
                        if os.path.exists(f):
                            os.remove(f)
                except Exception as e:
                    logger.warning(f"Error durante limpieza: {e}")

        encoded_filename = urllib.parse.quote(f"{titulo}.{ext}")

        return Response(
            generar_flujo_datos(),
            mimetype=mimetype_salida,
            headers={
                'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}",
            }
        )

    except Exception as e:
        logger.error(f"Excepción crítica: {traceback.format_exc()}")
        return f"Error interno del servidor: {str(e)}", 500

@app.route('/health')
def health():
    return {'status': 'operativo'}

if _name_ == '_main_':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
