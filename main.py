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
        h1 { color: #1a1a1a; font-size: 28px; font-weight: 700; margin-bottom: 10px; text-align: center; }
        .subtitle { color: #666; text-align: center; margin-bottom: 30px; font-size: 14px; }
        input[type="text"] {
            width: 100%; padding: 16px; border: 2px solid #e0e0e0;
            border-radius: 12px; font-size: 15px; margin-bottom: 15px;
            background: #f8f9fa; outline: none;
        }
        input[type="text"]:focus { border-color: #667eea; background: white; }
        button {
            width: 100%; padding: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border: none; border-radius: 12px;
            font-size: 16px; font-weight: 600; cursor: pointer; margin-bottom: 10px;
        }
        button:hover { transform: translateY(-2px); }
        button:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        .format-selector { display: flex; gap: 10px; margin-bottom: 15px; }
        .format-btn {
            flex: 1; padding: 12px; border: 2px solid #667eea;
            background: white; color: #667eea; border-radius: 10px;
            cursor: pointer; font-size: 14px;
        }
        .format-btn.active { background: #667eea; color: white; }
        .error-message {
            display: none; background: #fee; color: #c33;
            padding: 12px; border-radius: 8px; margin-top: 15px;
            text-align: center; font-size: 14px;
        }
        .error-message.active { display: block; }
        .loading { display: none; text-align: center; margin-top: 20px; }
        .loading.active { display: block; }
        .spinner {
            border: 3px solid #e0e0e0; border-top: 3px solid #667eea;
            border-radius: 50%; width: 40px; height: 40px;
            animation: spin 1s linear infinite; margin: 0 auto 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .info-text {
            font-size: 12px; color: #999; text-align: center; margin-top: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 YouTube Downloader</h1>
        <p class="subtitle">Descarga videos en MP4 compatible</p>
        
        <form id="downloadForm" onsubmit="handleSubmit(event)">
            <input type="text" id="urlInput" name="url" 
                   placeholder="Pega el enlace de YouTube aquí..." required>
            
            <div class="format-selector">
                <button type="button" class="format-btn active" 
                        onclick="selectFormat('video', this)">🎬 Video MP4</button>
                <button type="button" class="format-btn" 
                        onclick="selectFormat('audio', this)">🎵 Audio MP3</button>
            </div>
            
            <input type="hidden" id="formatInput" name="format" value="video">
            
            <button type="submit" id="downloadBtn">⬇️ Descargar Video MP4</button>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p id="loadingText">Descargando y convirtiendo a MP4...</p>
        </div>
        
        <div class="error-message" id="errorMessage"></div>
        <p class="info-text">Los videos se convierten automáticamente a MP4 compatible</p>
    </div>

    <script>
        let selectedFormat = 'video';
        
        function selectFormat(format, btn) {
            selectedFormat = format;
            document.getElementById('formatInput').value = format;
            document.querySelectorAll('.format-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const btn = document.getElementById('downloadBtn');
            const loadText = document.getElementById('loadingText');
            if (format === 'audio') {
                btn.textContent = '🎵 Descargar Audio MP3';
                loadText.textContent = 'Descargando y convirtiendo a MP3...';
            } else {
                btn.textContent = '⬇️ Descargar Video MP4';
                loadText.textContent = 'Descargando y convirtiendo a MP4...';
            }
        }
        
        function handleSubmit(event) {
            event.preventDefault();
            
            const url = document.getElementById('urlInput').value.trim();
            const downloadBtn = document.getElementById('downloadBtn');
            const loading = document.getElementById('loading');
            const errorMessage = document.getElementById('errorMessage');
            
            errorMessage.classList.remove('active');
            
            if (!url) {
                showError('Por favor, ingresa un enlace');
                return;
            }
            
            if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
                showError('Ingresa un enlace válido de YouTube');
                return;
            }
            
            downloadBtn.disabled = true;
            downloadBtn.textContent = '⏳ Procesando...';
            loading.classList.add('active');
            
            window.location.href = '/descargar?url=' + encodeURIComponent(url) + '&format=' + selectedFormat;
            
            setTimeout(() => {
                downloadBtn.disabled = false;
                downloadBtn.textContent = selectedFormat === 'audio' ? '🎵 Descargar Audio MP3' : '⬇️ Descargar Video MP4';
                loading.classList.remove('active');
            }, 20000);
        }
        
        function showError(message) {
            const errorMessage = document.getElementById('errorMessage');
            errorMessage.textContent = message;
            errorMessage.classList.add('active');
            setTimeout(() => errorMessage.classList.remove('active'), 5000);
        }
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
    """Convierte cualquier video a MP4 con H.264 usando ffmpeg"""
    archivo_salida = archivo_entrada.rsplit('.', 1)[0] + '_convertido.mp4'
    
    logger.info(f"Convirtiendo {archivo_entrada} a MP4 H.264...")
    
    comando = [
        'ffmpeg', '-i', archivo_entrada,
        '-c:v', 'libx264',      # Códec H.264
        '-preset', 'fast',       # Velocidad de conversión
        '-crf', '23',            # Calidad (menor = mejor)
        '-c:a', 'aac',           # Audio AAC
        '-b:a', '128k',          # Bitrate audio
        '-movflags', '+faststart', # Reproducción rápida
        '-y',                     # Sobrescribir
        archivo_salida
    ]
    
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True, timeout=300)
        if resultado.returncode == 0:
            logger.info(f"Conversión exitosa: {archivo_salida}")
            os.remove(archivo_entrada)  # Eliminar original
            return archivo_salida
        else:
            logger.error(f"Error ffmpeg: {resultado.stderr}")
            return None
    except Exception as e:
        logger.error(f"Error en conversión: {e}")
        return None

@app.route('/')
def inicio():
    return render_template_string(PAGINA_HTML)

@app.route('/descargar', methods=['GET'])
def descargar():
    try:
        video_url = request.args.get('url')
        formato = request.args.get('format', 'video')
        
        logger.info(f"Descargando: {video_url} - Formato: {formato}")
        
        if not video_url:
            return "Error: URL no proporcionada", 400

        if 'youtube.com' not in video_url and 'youtu.be' not in video_url:
            return "Error: URL no válida. Debe ser de YouTube", 400

        # Cargar cookies
        cargar_cookies()

        # Configuración base
        opciones = {
            'quiet': True,
            'no_warnings': True,
            'outtmpl': '/tmp/%(id)s.%(ext)s',
            'socket_timeout': 30,
            'retries': 3,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            },
        }

        if formato == 'audio':
            # Audio: descargar mejor audio y convertir a MP3
            opciones['format'] = 'bestaudio/best'
            opciones['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            # Video: intentar MP4 primero, si no, descargar lo mejor y convertir
            opciones['format'] = 'bestvideo+bestaudio/best'
            opciones['merge_output_format'] = 'mp4'

        # Añadir cookies si existen
        if os.path.exists(COOKIES_PATH):
            opciones['cookiefile'] = COOKIES_PATH

        # Descargar video
        logger.info("Iniciando descarga...")
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_id = info.get('id')
            titulo = info.get('title', 'video')
            # Limpiar título de caracteres problemáticos
            titulo = "".join(c for c in titulo if c.isalnum() or c in (' ', '-', '_')).rstrip()
            logger.info(f"Descargado: {titulo}")

        # Buscar archivo descargado
        archivos = glob.glob(f'/tmp/{video_id}.*')
        logger.info(f"Archivos encontrados: {archivos}")
        
        if not archivos:
            return "Error: No se encontró el archivo descargado", 500

        archivo = archivos[0]
        
        # Si es video y no es MP4, convertir a MP4 H.264
        if formato == 'video' and not archivo.endswith('.mp4'):
            logger.info(f"Archivo no es MP4 ({archivo}), convirtiendo...")
            nuevo_archivo = convertir_a_mp4(archivo)
            if nuevo_archivo:
                archivo = nuevo_archivo
            else:
                return "Error: No se pudo convertir el video a MP4 compatible", 500
        
        # Si es audio, asegurarse que sea MP3
        if formato == 'audio':
            # Buscar MP3
            mp3_archivos = [f for f in archivos if f.endswith('.mp3')]
            if mp3_archivos:
                archivo = mp3_archivos[0]
            elif archivos:
                archivo = archivos[0]

        ext = archivo.split('.')[-1]
        tamaño = os.path.getsize(archivo)
        logger.info(f"Archivo final: {archivo} ({tamaño} bytes)")

        def generar():
            try:
                with open(archivo, 'rb') as f:
                    while True:
                        chunk = f.read(1024 * 256)  # 256KB
                        if not chunk:
                            break
                        yield chunk
            finally:
                # Limpiar archivos temporales
                try:
                    if os.path.exists(archivo):
                        os.remove(archivo)
                    # Limpiar otros archivos del mismo video
                    for f in glob.glob(f'/tmp/{video_id}*'):
                        if os.path.exists(f):
                            os.remove(f)
                    logger.info("Archivos temporales eliminados")
                except Exception as e:
                    logger.error(f"Error limpiando: {e}")

        mime_types = {
            'mp4': 'video/mp4',
            'mp3': 'audio/mpeg',
            'webm': 'video/webm',
            'mkv': 'video/x-matroska',
        }

        return Response(
            generar(),
            mimetype=mime_types.get(ext, 'application/octet-stream'),
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
            return "Error: Video no disponible o es privado.", 500
        elif 'Private video' in error_msg:
            return "Error: Este video es privado.", 500
        else:
            return f"Error de descarga: {error_msg}", 500
            
    except Exception as e:
        logger.error(f"Error inesperado: {traceback.format_exc()}")
        return f"Error interno: {str(e)}", 500

@app.route('/health')
def health():
    """Verificar estado del servidor"""
    ffmpeg_disponible = False
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        ffmpeg_disponible = True
    except:
        pass
    
    return {
        'status': 'ok',
        'cookies': os.path.exists(COOKIES_PATH),
        'ffmpeg': ffmpeg_disponible
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Iniciando servidor en puerto {port}")
    app.run(host='0.0.0.0', port=port)
