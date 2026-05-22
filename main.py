import os
import glob
import yt_dlp
import traceback
import sys
import logging
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
        button:hover {
            transform: translateY(-2px);
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
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
        <h1>🎬 YouTube Downloader</h1>
        <p class="subtitle">Descarga videos en formato MP4 compatible</p>
        
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
            <p>Descargando y convirtiendo a MP4 compatible...</p>
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
                format === 'audio' ? '🎵 Descargar Audio MP3' : '⬇️ Descargar Video MP4';
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
            downloadBtn.textContent = '⏳ Descargando...';
            loading.classList.add('active');
            
            window.location.href = '/descargar?url=' + encodeURIComponent(url) + '&format=' + selectedFormat;
            
            setTimeout(() => {
                downloadBtn.disabled = false;
                downloadBtn.textContent = selectedFormat === 'audio' ? '🎵 Descargar Audio MP3' : '⬇️ Descargar Video MP4';
                loading.classList.remove('active');
            }, 15000);
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
            logger.info("Cargando cookies...")
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
        
        logger.info(f"Descargando: {video_url} - {formato}")
        
        if not video_url:
            return "Error: URL no proporcionada", 400

        # Cargar cookies
        cargar_cookies()

        # Configuración para MP4 compatible con H.264
        if formato == 'audio':
            opciones = {
                'quiet': True,
                'no_warnings': True,
                'outtmpl': '/tmp/%(id)s.%(ext)s',
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'socket_timeout': 30,
                'retries': 3,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                },
            }
        else:
            # VIDEO: Forzar MP4 con códec H.264 compatible
            opciones = {
                'quiet': True,
                'no_warnings': True,
                'outtmpl': '/tmp/%(id)s.%(ext)s',
                # Descargar mejor video MP4 y mejor audio, luego combinar
                'format': 'bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',  # Forzar MP4 como salida
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',  # Convertir a MP4 si es necesario
                }],
                'socket_timeout': 30,
                'retries': 3,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                },
            }

        # Añadir cookies si existen
        if os.path.exists(COOKIES_PATH):
            opciones['cookiefile'] = COOKIES_PATH

        # Descargar
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_id = info.get('id')
            titulo = info.get('title', 'video')
            titulo = "".join(c for c in titulo if c.isalnum() or c in (' ', '-', '_')).rstrip()

        # Buscar archivo (preferir .mp4)
        archivos = glob.glob(f'/tmp/{video_id}.*')
        
        # Priorizar MP4
        archivo = None
        for f in archivos:
            if f.endswith('.mp4') or f.endswith('.mp3'):
                archivo = f
                break
        if not archivo and archivos:
            archivo = archivos[0]
        
        if not archivo:
            return "Error: Archivo no encontrado", 500

        ext = archivo.split('.')[-1]
        tamaño = os.path.getsize(archivo)
        logger.info(f"Archivo final: {archivo} ({tamaño} bytes) - Formato: {ext}")

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
                    if os.path.exists(archivo):
                        os.remove(archivo)
                except:
                    pass

        # MIME types correctos
        mime_types = {
            'mp4': 'video/mp4',
            'mp3': 'audio/mpeg',
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
        logger.error(f"Error: {error_msg}")
        if 'Sign in to confirm' in error_msg:
            return "Error: YouTube requiere cookies. Configura YOUTUBE_COOKIES en Railway.", 500
        return f"Error de descarga: {error_msg}", 500
            
    except Exception as e:
        logger.error(f"Error: {traceback.format_exc()}")
        return f"Error: {str(e)}", 500

@app.route('/health')
def health():
    return {'status': 'ok', 'cookies': os.path.exists(COOKIES_PATH)}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
