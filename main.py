import os
import glob
import yt_dlp
import traceback
import sys
from flask import Flask, render_template_string, request, Response

app = Flask(__name__)
COOKIES_PATH = '/tmp/cookies.txt'

# Configurar logging para ver errores detallados
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

PAGINA_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Downloader</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

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
            max-width: 480px;
            width: 100%;
        }

        .logo {
            text-align: center;
            margin-bottom: 10px;
        }

        .logo-icon {
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #ff0000 0%, #cc0000 100%);
            border-radius: 16px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 15px;
        }

        .logo-icon::before {
            content: "▶";
            color: white;
            font-size: 28px;
            margin-left: 4px;
        }

        h1 {
            color: #1a1a1a;
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
            text-align: center;
        }

        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
            font-size: 14px;
        }

        .input-group {
            position: relative;
            margin-bottom: 20px;
        }

        input[type="text"] {
            width: 100%;
            padding: 16px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            font-size: 15px;
            background: #f8f9fa;
            color: #333;
            outline: none;
        }

        input[type="text"]:focus {
            border-color: #667eea;
            background: white;
        }

        button {
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
        }

        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .format-selector {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }

        .format-btn {
            flex: 1;
            padding: 10px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
        }

        .format-btn.active {
            background: #667eea;
            color: white;
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

        .error-message.active {
            display: block;
        }

        .loading {
            display: none;
            text-align: center;
            margin-top: 20px;
            color: #666;
        }

        .loading.active {
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
        <div class="logo">
            <div class="logo-icon"></div>
        </div>
        <h1>YouTube Downloader</h1>
        <p class="subtitle">Descarga videos de YouTube fácilmente</p>
        
        <form id="downloadForm" onsubmit="handleSubmit(event)">
            <input type="text" id="urlInput" name="url" placeholder="Pega el enlace de YouTube aquí..." required>
            
            <div class="format-selector">
                <button type="button" class="format-btn active" onclick="selectFormat('video', this)">🎬 Video</button>
                <button type="button" class="format-btn" onclick="selectFormat('audio', this)">🎵 Audio MP3</button>
            </div>
            
            <input type="hidden" id="formatInput" name="format" value="video">
            
            <button type="submit" id="downloadBtn">⬇️ Descargar</button>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Descargando, por favor espera...</p>
        </div>
        
        <div class="error-message" id="errorMessage"></div>
    </div>

    <script>
        let selectedFormat = 'video';
        
        function selectFormat(format, btn) {
            selectedFormat = format;
            document.getElementById('formatInput').value = format;
            document.querySelectorAll('.format-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById('downloadBtn').textContent = 
                format === 'audio' ? '🎵 Descargar Audio MP3' : '⬇️ Descargar Video';
        }
        
        function handleSubmit(event) {
            event.preventDefault();
            
            const urlInput = document.getElementById('urlInput');
            const downloadBtn = document.getElementById('downloadBtn');
            const loading = document.getElementById('loading');
            const errorMessage = document.getElementById('errorMessage');
            
            errorMessage.classList.remove('active');
            errorMessage.textContent = '';
            
            const url = urlInput.value.trim();
            
            if (!url) {
                showError('Por favor, ingresa un enlace de YouTube');
                return;
            }
            
            if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
                showError('Por favor, ingresa un enlace válido de YouTube');
                return;
            }
            
            downloadBtn.disabled = true;
            downloadBtn.textContent = '⏳ Descargando...';
            loading.classList.add('active');
            
            window.location.href = '/descargar?url=' + encodeURIComponent(url) + '&format=' + selectedFormat;
            
            setTimeout(() => {
                downloadBtn.disabled = false;
                downloadBtn.textContent = selectedFormat === 'audio' ? '🎵 Descargar Audio MP3' : '⬇️ Descargar Video';
                loading.classList.remove('active');
            }, 10000);
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
            logger.info("Cargando cookies desde variable de entorno...")
            with open(COOKIES_PATH, 'w', encoding='utf-8') as f:
                f.write(cookies_env)
            logger.info(f"Cookies guardadas en {COOKIES_PATH}")
            return True
        else:
            logger.warning("No se encontró la variable YOUTUBE_COOKIES")
            return False
    except Exception as e:
        logger.error(f"Error al cargar cookies: {str(e)}")
        return False

def configurar_opciones(formato='video'):
    """Configura las opciones de yt-dlp"""
    logger.info(f"Configurando opciones para formato: {formato}")
    
    opciones = {
        'quiet': False,  # Cambiado a False para ver logs
        'no_warnings': False,
        'verbose': True,  # Más detalles
        'outtmpl': '/tmp/%(id)s.%(ext)s',
        'socket_timeout': 30,
        'retries': 3,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        },
    }
    
    # Formato simple y compatible
    if formato == 'audio':
        opciones['format'] = 'bestaudio/best'
        opciones['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        # Usar formatos simples y compatibles
        opciones['format'] = 'best[height<=720]/best'
    
    # Añadir cookies si existen
    if os.path.exists(COOKIES_PATH):
        opciones['cookiefile'] = COOKIES_PATH
        logger.info("Usando archivo de cookies")
    
    return opciones

@app.route('/')
def inicio():
    logger.info("Sirviendo página principal")
    return render_template_string(PAGINA_HTML)

@app.route('/descargar', methods=['GET'])
def descargar():
    try:
        video_url = request.args.get('url')
        formato = request.args.get('format', 'video')
        
        logger.info(f"Iniciando descarga - URL: {video_url}, Formato: {formato}")
        
        if not video_url:
            logger.error("No se proporcionó URL")
            return "Error: No se proporcionó una URL", 400

        # Validar URL
        if 'youtube.com' not in video_url and 'youtu.be' not in video_url:
            logger.error(f"URL no válida: {video_url}")
            return "Error: URL no válida", 400

        # Verificar que /tmp existe y es escribible
        if not os.path.exists('/tmp'):
            logger.error("Directorio /tmp no existe")
            return "Error: Directorio temporal no disponible", 500
        
        # Cargar cookies
        cargar_cookies()

        # Configurar opciones
        opciones = configurar_opciones(formato)
        
        logger.info("Opciones configuradas, iniciando descarga...")
        
        # Descargar video
        with yt_dlp.YoutubeDL(opciones) as ydl:
            logger.info("Extrayendo información del video...")
            info = ydl.extract_info(video_url, download=True)
            video_id = info.get('id')
            titulo = info.get('title', 'video')
            # Limpiar título
            titulo = "".join(c for c in titulo if c.isalnum() or c in (' ', '-', '_')).rstrip()
            logger.info(f"Video descargado: {titulo} (ID: {video_id})")

        # Buscar archivo descargado
        logger.info(f"Buscando archivos para ID: {video_id}")
        archivos = glob.glob(f'/tmp/{video_id}.*')
        logger.info(f"Archivos encontrados: {archivos}")
        
        if not archivos:
            logger.error("No se encontró el archivo descargado")
            return "Error: No se encontró el archivo descargado", 500

        archivo = archivos[0]
        ext = archivo.split('.')[-1]
        tamaño = os.path.getsize(archivo)
        logger.info(f"Archivo seleccionado: {archivo} ({tamaño} bytes)")

        def generar():
            try:
                with open(archivo, 'rb') as f:
                    while True:
                        chunk = f.read(8192)  # Chunks más pequeños
                        if not chunk:
                            break
                        yield chunk
            except Exception as e:
                logger.error(f"Error durante el streaming: {str(e)}")
            finally:
                try:
                    if os.path.exists(archivo):
                        os.remove(archivo)
                        logger.info(f"Archivo temporal eliminado: {archivo}")
                except Exception as e:
                    logger.error(f"Error al eliminar archivo: {str(e)}")

        logger.info("Iniciando streaming del archivo...")
        return Response(
            generar(),
            mimetype='application/octet-stream',
            headers={
                'Content-Disposition': f'attachment; filename="{titulo}.{ext}"',
                'Content-Length': str(tamaño),
            }
        )

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        logger.error(f"Error de yt-dlp: {error_msg}")
        
        if 'Sign in to confirm' in error_msg:
            return "Error: YouTube requiere autenticación. Configura las cookies.", 500
        elif 'Video unavailable' in error_msg:
            return "Error: Video no disponible", 500
        elif 'Requested format is not available' in error_msg:
            return "Error: Formato no disponible para este video", 500
        else:
            return f"Error de descarga: {error_msg}", 500
            
    except Exception as e:
        error_detallado = traceback.format_exc()
        logger.error(f"Error inesperado: {error_detallado}")
        return f"Error interno del servidor: {str(e)}", 500

@app.route('/test')
def test():
    """Endpoint de prueba para verificar que el servidor funciona"""
    try:
        # Verificar componentes
        checks = {
            'python_version': sys.version,
            'flask_working': True,
            'tmp_exists': os.path.exists('/tmp'),
            'tmp_writable': os.access('/tmp', os.W_OK),
            'cookies_env': 'YOUTUBE_COOKIES' in os.environ,
            'cookies_file': os.path.exists(COOKIES_PATH),
            'yt_dlp_version': yt_dlp.version.__version__,
        }
        
        # Verificar si hay cookies
        if checks['cookies_env']:
            cookies_len = len(os.environ.get('YOUTUBE_COOKIES', ''))
            checks['cookies_length'] = cookies_len
        
        return checks
        
    except Exception as e:
        return {'error': str(e), 'traceback': traceback.format_exc()}, 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Iniciando servidor en puerto {port}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"yt-dlp version: {yt_dlp.version.__version__}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )
