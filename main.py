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
            padding: 40px;
            max-width: 500px;
            width: 100%;
        }
        h1 { 
            color: #1a1a1a; 
            font-size: 28px; 
            font-weight: 700; 
            margin-bottom: 10px; 
            text-align: center; 
        }
        .subtitle { 
            color: #666; 
            text-align: center; 
            margin-bottom: 30px; 
            font-size: 14px; 
        }
        input[type="text"] {
            width: 100%; 
            padding: 16px; 
            border: 2px solid #e0e0e0;
            border-radius: 12px; 
            font-size: 15px; 
            margin-bottom: 15px;
            background: #f8f9fa; 
            outline: none;
        }
        input[type="text"]:focus { 
            border-color: #667eea; 
            background: white; 
        }
        .format-selector { 
            display: flex; 
            gap: 10px; 
            margin-bottom: 15px; 
        }
        .format-btn {
            flex: 1; 
            padding: 12px; 
            border: 2px solid #667eea;
            background: white; 
            color: #667eea; 
            border-radius: 10px;
            cursor: pointer; 
            font-size: 14px;
            transition: all 0.3s;
        }
        .format-btn.active { 
            background: #667eea; 
            color: white; 
        }
        .format-btn:hover {
            background: #667eea;
            color: white;
        }
        button[type="submit"] {
            width: 100%; 
            padding: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            border: none; 
            border-radius: 12px;
            font-size: 16px; 
            font-weight: 600; 
            cursor: pointer; 
            margin-bottom: 10px;
            transition: transform 0.2s;
        }
        button[type="submit"]:hover { 
            transform: translateY(-2px); 
        }
        button[type="submit"]:active { 
            transform: translateY(0); 
        }
        .error-message {
            display: none; 
            background: #fee; 
            color: #c33;
            padding: 12px; 
            border-radius: 8px; 
            margin-top: 15px;
            text-align: center; 
            font-size: 14px;
        }
        .error-message.show { 
            display: block; 
        }
        .loading {
            display: none; 
            text-align: center; 
            margin-top: 20px;
        }
        .loading.show { 
            display: block; 
        }
        .spinner {
            border: 3px solid #e0e0e0; 
            border-top: 3px solid #667eea;
            border-radius: 50%; 
            width: 40px; 
            height: 40px;
            animation: spin 1s linear infinite; 
            margin: 0 auto 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 YouTube Downloader</h1>
        <p class="subtitle">Descarga videos en MP4 compatible</p>
        
        <form id="downloadForm" method="GET" action="/descargar">
            <input type="text" id="urlInput" name="url" 
                   placeholder="Pega el enlace de YouTube aquí..." required>
            
            <div class="format-selector">
                <button type="button" id="videoBtn" class="format-btn active" 
                        onclick="selectFormat('video')">🎬 Video MP4</button>
                <button type="button" id="audioBtn" class="format-btn" 
                        onclick="selectFormat('audio')">🎵 Audio MP3</button>
            </div>
            
            <input type="hidden" id="formatInput" name="format" value="video">
            
            <button type="submit" id="downloadBtn">⬇️ Descargar Video MP4</button>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>⏳ Descargando, por favor espera...</p>
        </div>
        
        <div class="error-message" id="errorMessage"></div>
    </div>

    <script>
        function selectFormat(format) {
            document.getElementById('formatInput').value = format;
            document.getElementById('videoBtn').classList.remove('active');
            document.getElementById('audioBtn').classList.remove('active');
            
            if (format === 'video') {
                document.getElementById('videoBtn').classList.add('active');
                document.getElementById('downloadBtn').textContent = '⬇️ Descargar Video MP4';
            } else {
                document.getElementById('audioBtn').classList.add('active');
                document.getElementById('downloadBtn').textContent = '🎵 Descargar Audio MP3';
            }
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
        
        logger.info(f"Descargando: {video_url} - {formato}")
        
        if not video_url:
            return "Error: URL no proporcionada", 400

        if 'youtube.com' not in video_url and 'youtu.be' not in video_url:
            return "Error: URL no válida", 400

        cargar_cookies()

        # Configuración SIMPLE - descargar lo que esté disponible
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
            # Solo audio
            opciones['format'] = 'bestaudio/best'
            opciones['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            # VIDEO: Descargar el mejor formato único que incluya video y audio
            # Si no existe, descargar video y audio por separado
            opciones['format'] = 'best'  # El mejor formato único con video+audio

        if os.path.exists(COOKIES_PATH):
            opciones['cookiefile'] = COOKIES_PATH

        # Primer intento con formato simple
        try:
            with yt_dlp.YoutubeDL(opciones) as ydl:
                info = ydl.extract_info(video_url, download=True)
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Primer intento falló: {error_msg}")
            
            # Si falla, intentar descargar video y audio por separado
            if 'Requested format is not available' in error_msg and formato == 'video':
                logger.info("Intentando descargar video y audio por separado...")
                opciones['format'] = 'bestvideo*+bestaudio/bestvideo+bestaudio'
                try:
                    with yt_dlp.YoutubeDL(opciones) as ydl:
                        info = ydl.extract_info(video_url, download=True)
                except:
                    # Último intento: cualquier formato disponible
                    opciones['format'] = 'bestvideo,bestaudio/best'
                    with yt_dlp.YoutubeDL(opciones) as ydl:
                        info = ydl.extract_info(video_url, download=True)
            else:
                raise e

        video_id = info.get('id')
        titulo = info.get('title', 'video')
        titulo = "".join(c for c in titulo if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        logger.info(f"Descargado: {titulo}")

        # Buscar todos los archivos descargados
        archivos = glob.glob(f'/tmp/{video_id}.*')
        logger.info(f"Archivos encontrados: {archivos}")
        
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
                # Si no hay MP4, usar el primer archivo y convertir
                archivo = archivos[0]
                if not archivo.endswith('.mp4'):
                    nuevo = convertir_a_mp4(archivo)
                    if nuevo:
                        archivo = nuevo
                    else:
                        return "Error: No se pudo convertir a MP4", 500

        ext = archivo.split('.')[-1]
        tamaño = os.path.getsize(archivo)
        logger.info(f"Archivo final: {archivo} ({tamaño} bytes)")

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
        logger.error(f"Error descarga: {error_msg}")
        
        if 'Sign in to confirm' in error_msg:
            return "Error: YouTube requiere autenticación. Configura YOUTUBE_COOKIES en Railway.", 500
        elif 'Video unavailable' in error_msg:
            return "Error: Video no disponible o privado.", 500
        else:
            return f"Error de descarga: {error_msg}", 500
            
    except Exception as e:
        logger.error(f"Error: {traceback.format_exc()}")
        return f"Error interno: {str(e)}", 500

@app.route('/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
