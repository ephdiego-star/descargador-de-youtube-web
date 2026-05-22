import os
import glob
import yt_dlp
import traceback
import sys
import logging
import subprocess
from flask import Flask, render_template_string, request, Response

app = Flask(__name__)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

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
                        onclick="selectFormat('video')">🎬 Video MP4</button>
                <button type="button" id="audioBtn" class="format-btn" 
                        onclick="selectFormat('audio')">🎵 Audio MP3</button>
            </div>
            
            <p class="section-title">📺 Calidad de video:</p>
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
            
            // Reset all quality buttons
            document.querySelectorAll('.quality-btn').forEach(function(btn) {
                btn.classList.remove('active');
            });
            
            // Activate selected
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
                errorDiv.textContent = '❌ Por favor, ingresa un enlace de YouTube';
                errorDiv.classList.add('show');
                return false;
            }
            
            if (url.indexOf('youtube.com') === -1 && url.indexOf('youtu.be') === -1) {
                e.preventDefault();
                errorDiv.textContent = '❌ Ingresa un enlace válido de YouTube';
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
            logger.info("Cookies cargadas")
            return True
        return False
    except Exception as e:
        logger.error(f"Error cookies: {e}")
        return False

def convertir_a_mp4(archivo_entrada):
    """Convierte video a MP4 con H.264"""
    archivo_salida = archivo_entrada.rsplit('.', 1)[0] + '.mp4'
    
    logger.info(f"Convirtiendo a MP4: {archivo_entrada}")
    
    comando = [
        'ffmpeg', '-i', archivo_entrada,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-movflags', '+faststart',
        '-y',
        archivo_salida
    ]
    
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, timeout=300)
        if resultado.returncode == 0:
            os.remove(archivo_entrada)
            return archivo_salida
        return None
    except Exception as e:
        logger.error(f"Error conversión: {e}")
        return None

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

        # Configuración base
        opciones = {
            'quiet': True,
            'no_warnings': True,
            'outtmpl': '/tmp/%(id)s.%(ext)s',
            'socket_timeout': 30,
            'retries': 5,
            'fragment_retries': 5,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
        }

        if formato == 'audio':
            # Audio: ignora calidad
            opciones['format'] = 'bestaudio/best'
            opciones['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            # Video con calidad seleccionada
            # Sistema de fallback automático
            formatos_por_calidad = {
                '1080p': [
                    'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
                    'bestvideo[height<=720]+bestaudio/best[height<=720]',
                    'best',
                ],
                '720p': [
                    'bestvideo[height<=720]+bestaudio/best[height<=720]',
                    'bestvideo[height<=480]+bestaudio/best[height<=480]',
                    'best',
                ],
                '480p': [
                    'bestvideo[height<=480]+bestaudio/best[height<=480]',
                    'bestvideo[height<=360]+bestaudio/best[height<=360]',
                    'best',
                ],
                '360p': [
                    'bestvideo[height<=360]+bestaudio/best[height<=360]',
                    'worst',
                ],
                'best': ['best'],
            }
            
            formatos = formatos_por_calidad.get(calidad, formatos_por_calidad['720p'])
            opciones['format'] = '/'.join(formatos)  # yt-dlp probará cada uno en orden

        if os.path.exists(COOKIES_PATH):
            opciones['cookiefile'] = COOKIES_PATH

        # Descargar con múltiples intentos
        logger.info(f"Intentando formatos: {opciones['format']}")
        
        try:
            with yt_dlp.YoutubeDL(opciones) as ydl:
                info = ydl.extract_info(video_url, download=True)
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Falló con calidad {calidad}: {error_msg}")
            
            # Si falla, intentar con 'best'
            if 'Requested format is not available' in error_msg:
                logger.info("Intentando con mejor calidad disponible...")
                opciones['format'] = 'best'
                try:
                    with yt_dlp.YoutubeDL(opciones) as ydl:
                        info = ydl.extract_info(video_url, download=True)
                except:
                    # Último intento
                    opciones['format'] = 'worst'
                    with yt_dlp.YoutubeDL(opciones) as ydl:
                        info = ydl.extract_info(video_url, download=True)
            else:
                raise e

        video_id = info.get('id')
        titulo = info.get('title', 'video')
        titulo = "".join(c for c in titulo if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        # Obtener altura real del video descargado
        altura_real = info.get('height', '?')
        logger.info(f"Descargado: {titulo} - Altura real: {altura_real}p")

        # Buscar archivos
        archivos = glob.glob(f'/tmp/{video_id}.*')
        
        if not archivos:
            return "Error: No se encontró el archivo", 500

        # Para audio, buscar MP3
        if formato == 'audio':
            archivos_mp3 = [f for f in archivos if f.endswith('.mp3')]
            archivo = archivos_mp3[0] if archivos_mp3 else archivos[0]
        else:
            # Para video, preferir MP4
            archivos_mp4 = [f for f in archivos if f.endswith('.mp4')]
            if archivos_mp4:
                archivo = archivos_mp4[0]
            else:
                archivo = archivos[0]
                if not archivo.endswith('.mp4'):
                    nuevo = convertir_a_mp4(archivo)
                    if nuevo:
                        archivo = nuevo

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

        mime_type = 'video/mp4' if ext == 'mp4' else 'audio/mpeg'

        return Response(
            generar(),
            mimetype=mime_type,
            headers={
                'Content-Disposition': f'attachment; filename="{titulo}.{ext}"',
                'Content-Length': str(tamaño),
            }
        )

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        logger.error(f"Error: {error_msg}")
        
        if 'Sign in to confirm' in error_msg:
            return "Error: YouTube requiere autenticación. Configura YOUTUBE_COOKIES en Railway.", 500
        elif 'Video unavailable' in error_msg:
            return "Error: Video no disponible o privado.", 500
        else:
            return f"Error: {error_msg}", 500
            
    except Exception as e:
        logger.error(f"Error: {traceback.format_exc()}")
        return f"Error: {str(e)}", 500

@app.route('/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
