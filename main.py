import os
import glob
import yt_dlp
from flask import Flask, render_template_string, request, Response

app = Flask(__name__)
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
            animation: gradientBG 15s ease infinite;
            background-size: 400% 400%;
        }

        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            padding: 40px;
            max-width: 480px;
            width: 100%;
            backdrop-filter: blur(10px);
            transform: translateY(0);
            transition: transform 0.3s ease;
        }

        .container:hover {
            transform: translateY(-5px);
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
            box-shadow: 0 10px 20px rgba(255, 0, 0, 0.3);
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
            font-weight: 400;
        }

        .input-group {
            position: relative;
            margin-bottom: 20px;
        }

        .input-icon {
            position: absolute;
            left: 16px;
            top: 50%;
            transform: translateY(-50%);
            color: #999;
            font-size: 20px;
            transition: color 0.3s ease;
        }

        input[type="text"] {
            width: 100%;
            padding: 16px 16px 16px 48px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            font-size: 15px;
            transition: all 0.3s ease;
            background: #f8f9fa;
            color: #333;
            outline: none;
        }

        input[type="text"]:focus {
            border-color: #667eea;
            background: white;
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
        }

        input[type="text"]::placeholder {
            color: #999;
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
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            letter-spacing: 0.5px;
        }

        button::before {
            content: "";
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s ease;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }

        button:hover::before {
            left: 100%;
        }

        button:active {
            transform: translateY(0);
        }

        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
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

        .progress-bar {
            display: none;
            width: 100%;
            height: 6px;
            background: #e0e0e0;
            border-radius: 3px;
            margin-top: 15px;
            overflow: hidden;
        }

        .progress-bar.active {
            display: block;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            border-radius: 3px;
            animation: progress 2s ease-in-out infinite;
        }

        @keyframes progress {
            0% { width: 0%; }
            50% { width: 70%; }
            100% { width: 100%; }
        }

        .quality-selector {
            margin: 20px 0;
            display: flex;
            gap: 10px;
            justify-content: center;
            flex-wrap: wrap;
        }

        .quality-btn {
            padding: 8px 16px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.3s ease;
        }

        .quality-btn.active {
            background: #667eea;
            color: white;
        }

        .format-selector {
            margin: 20px 0;
            display: flex;
            gap: 10px;
            justify-content: center;
        }

        .format-btn {
            padding: 8px 16px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
        }

        .format-btn.active {
            background: #667eea;
            color: white;
        }

        .features {
            display: flex;
            justify-content: space-around;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }

        .feature {
            text-align: center;
            color: #666;
            font-size: 12px;
            transition: transform 0.3s ease;
        }

        .feature:hover {
            transform: translateY(-3px);
        }

        .feature-icon {
            font-size: 24px;
            margin-bottom: 5px;
            display: block;
        }

        .version {
            text-align: center;
            color: #999;
            font-size: 11px;
            margin-top: 20px;
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

        @media (max-width: 480px) {
            .container {
                padding: 30px 20px;
            }
            
            h1 {
                font-size: 24px;
            }
            
            .features {
                flex-wrap: wrap;
                gap: 15px;
            }
            
            .quality-selector {
                gap: 5px;
            }
            
            .quality-btn {
                padding: 6px 12px;
                font-size: 12px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <div class="logo-icon"></div>
        </div>
        <h1>YouTube Downloader</h1>
        <p class="subtitle">Descarga tus videos favoritos al instante</p>
        
        <form id="downloadForm" onsubmit="handleSubmit(event)">
            <div class="input-group">
                <span class="input-icon">🔗</span>
                <input type="text" id="urlInput" name="url" placeholder="Pega el enlace de YouTube aquí..." required>
            </div>
            
            <div class="format-selector">
                <button type="button" class="format-btn active" onclick="selectFormat('video', this)">🎬 Video</button>
                <button type="button" class="format-btn" onclick="selectFormat('audio', this)">🎵 Audio</button>
            </div>
            
            <div class="quality-selector" id="qualitySelector">
                <button type="button" class="quality-btn" onclick="selectQuality('best', this)">✨ Mejor</button>
                <button type="button" class="quality-btn active" onclick="selectQuality('720p', this)">HD 720p</button>
                <button type="button" class="quality-btn" onclick="selectQuality('480p', this)">SD 480p</button>
                <button type="button" class="quality-btn" onclick="selectQuality('360p', this)">Baja 360p</button>
            </div>
            
            <input type="hidden" id="formatInput" name="format" value="video">
            <input type="hidden" id="qualityInput" name="quality" value="720p">
            
            <button type="submit" id="downloadBtn">⬇️ Descargar Video</button>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p id="loadingText">Preparando descarga...</p>
            <p style="font-size: 12px; color: #999;">Buscando mejor calidad disponible...</p>
        </div>
        
        <div class="progress-bar" id="progressBar">
            <div class="progress-fill"></div>
        </div>
        
        <div class="error-message" id="errorMessage"></div>
        
        <div class="features">
            <div class="feature">
                <span class="feature-icon">📱</span>
                Móvil
            </div>
            <div class="feature">
                <span class="feature-icon">💻</span>
                PC
            </div>
            <div class="feature">
                <span class="feature-icon">📟</span>
                Tablet
            </div>
            <div class="feature">
                <span class="feature-icon">⚡</span>
                Rápido
            </div>
        </div>
        
        <div class="version">v3.0 • YouTube Downloader</div>
    </div>

    <script>
        let selectedFormat = 'video';
        let selectedQuality = '720p';
        
        function selectFormat(format, btn) {
            selectedFormat = format;
            document.getElementById('formatInput').value = format;
            
            // Actualizar botones de formato
            document.querySelectorAll('.format-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Mostrar/ocultar selector de calidad
            const qualitySelector = document.getElementById('qualitySelector');
            qualitySelector.style.display = format === 'video' ? 'flex' : 'none';
            
            // Actualizar texto del botón
            updateDownloadButton();
        }
        
        function selectQuality(quality, btn) {
            selectedQuality = quality;
            document.getElementById('qualityInput').value = quality;
            
            // Actualizar botones de calidad
            document.querySelectorAll('.quality-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            updateDownloadButton();
        }
        
        function updateDownloadButton() {
            const downloadBtn = document.getElementById('downloadBtn');
            const loadingText = document.getElementById('loadingText');
            
            if (selectedFormat === 'audio') {
                downloadBtn.textContent = '🎵 Descargar Audio MP3';
                loadingText.textContent = 'Descargando audio...';
            } else {
                const qualityLabels = {
                    'best': 'Mejor calidad',
                    '720p': 'HD 720p',
                    '480p': 'SD 480p',
                    '360p': 'Baja 360p'
                };
                downloadBtn.textContent = '⬇️ Descargar Video (' + qualityLabels[selectedQuality] + ')';
                loadingText.textContent = 'Descargando video en ' + qualityLabels[selectedQuality] + '...';
            }
        }
        
        function handleSubmit(event) {
            event.preventDefault();
            
            const urlInput = document.getElementById('urlInput');
            const downloadBtn = document.getElementById('downloadBtn');
            const loading = document.getElementById('loading');
            const progressBar = document.getElementById('progressBar');
            const errorMessage = document.getElementById('errorMessage');
            
            // Reset estados
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
            
            // Mostrar loading
            downloadBtn.disabled = true;
            downloadBtn.textContent = '⏳ Buscando video...';
            loading.classList.add('active');
            progressBar.classList.add('active');
            
            // Construir URL
            let downloadUrl = '/descargar?url=' + encodeURIComponent(url) + '&format=' + selectedFormat;
            if (selectedFormat === 'video') {
                downloadUrl += '&quality=' + selectedQuality;
            }
            
            // Iniciar descarga
            window.location.href = downloadUrl;
            
            // Timeout para restaurar botón
            setTimeout(() => {
                downloadBtn.disabled = false;
                updateDownloadButton();
                loading.classList.remove('active');
                progressBar.classList.remove('active');
            }, 15000);
        }
        
        function showError(message) {
            const errorMessage = document.getElementById('errorMessage');
            errorMessage.textContent = message;
            errorMessage.classList.add('active');
            setTimeout(() => {
                errorMessage.classList.remove('active');
            }, 5000);
        }
        
        // Inicializar texto del botón
        updateDownloadButton();
    </script>
</body>
</html>
"""

def cargar_cookies():
    """Carga las cookies desde variable de entorno o archivo"""
    cookies_env = os.environ.get('YOUTUBE_COOKIES')
    if cookies_env:
        try:
            with open(COOKIES_PATH, 'w', encoding='utf-8') as f:
                f.write(cookies_env)
            return True
        except Exception as e:
            print(f"Error guardando cookies: {e}")
            return False
    return False

def configurar_opciones(formato='video', calidad='720p'):
    """Configura las opciones de yt-dlp con formato flexible"""
    
    # Configuración base
    opciones = {
        'quiet': True,
        'no_warnings': True,
        'outtmpl': '/tmp/%(id)s.%(ext)s',
        'socket_timeout': 30,
        'retries': 5,
        'extractor_retries': 3,
        'fragment_retries': 5,
        'retry_sleep_functions': {
            'http': lambda n: 2,
            'fragment': lambda n: 1,
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        },
    }
    
    # Configurar formato según selección
    if formato == 'audio':
        # Solo audio, el mejor disponible
        opciones['format'] = 'bestaudio/best'
        opciones['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        # Video con calidad seleccionada, con fallback automático
        formatos_por_calidad = {
            'best': [
                'bv*+ba/b',                    # Mejor video + mejor audio
                'bv+ba/b',                     # Alternativa
                'best',                        # Mejor formato único
            ],
            '720p': [
                'bv*[height<=720]+ba/b',       # 720p combinado
                'bv[height<=720]+ba/b',        # Alternativa 720p
                'bv*[height<=720]',            # Solo video 720p
                'best[height<=720]',           # Mejor hasta 720p
                'worst[height>=720]',          # Peor que sea al menos 720p
                'best',                        # Cualquier cosa
            ],
            '480p': [
                'bv*[height<=480]+ba/b',
                'bv[height<=480]+ba/b',
                'best[height<=480]',
                'worst[height>=480]',
                'best',
            ],
            '360p': [
                'bv*[height<=360]+ba/b',
                'bv[height<=360]+ba/b',
                'best[height<=360]',
                'worst[height>=360]',
                'best',
            ],
        }
        
        # Usar lista de formatos con fallback automático
        formatos = formatos_por_calidad.get(calidad, formatos_por_calidad['720p'])
        opciones['format'] = '/'.join(formatos)  # yt-dlp probará cada formato en orden
    
    # Añadir cookies si existen
    if os.path.exists(COOKIES_PATH):
        opciones['cookiefile'] = COOKIES_PATH
        print("Usando archivo de cookies")
    
    # Intentar diferentes clientes si falla
    opciones['extractor_args'] = {
        'youtube': {
            'player_client': ['android', 'web', 'mweb'],
        }
    }
    
    return opciones

@app.route('/')
def inicio():
    return render_template_string(PAGINA_HTML)

@app.route('/descargar', methods=['GET'])
def descargar():
    video_url = request.args.get('url')
    formato = request.args.get('format', 'video')
    calidad = request.args.get('quality', '720p')
    
    if not video_url:
        return "Error: No se proporcionó una URL", 400

    # Validar URL de YouTube
    if 'youtube.com' not in video_url and 'youtu.be' not in video_url:
        return "Error: URL no válida. Debe ser un enlace de YouTube", 400

    # Cargar cookies
    cookies_cargadas = cargar_cookies()
    
    if not cookies_cargadas and not os.path.exists(COOKIES_PATH):
        print("ADVERTENCIA: No se encontraron cookies. YouTube puede requerir autenticación.")

    # Configurar opciones con el formato flexible
    opciones = configurar_opciones(formato, calidad)

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_id = info.get('id')
            titulo = info.get('title', 'video').replace('/', '-').replace('\\', '-')
            
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        
        # Intentar con formato más básico si falla
        if 'Requested format is not available' in error_msg:
            try:
                print("Formato solicitado no disponible, intentando con mejor calidad disponible...")
                opciones['format'] = 'best'
                with yt_dlp.YoutubeDL(opciones) as ydl:
                    info = ydl.extract_info(video_url, download=True)
                    video_id = info.get('id')
                    titulo = info.get('title', 'video').replace('/', '-').replace('\\', '-')
            except Exception as e2:
                return f"Error: No se pudo descargar el video en ningún formato. Puede estar restringido.", 500
        elif 'Sign in to confirm' in error_msg:
            return "Error: YouTube requiere autenticación. El servidor necesita cookies válidas.", 500
        elif 'Video unavailable' in error_msg:
            return "Error: Video no disponible. Puede ser privado o eliminado.", 500
        else:
            return f"Error de descarga: {error_msg}", 500
        
    except Exception as e:
        return f"Error técnico: {str(e)}", 500

    # Buscar el archivo descargado
    patrones = [
        f'/tmp/{video_id}.*',
        f'/tmp/{video_id}.mp3',
        f'/tmp/{video_id}.webm',
        f'/tmp/{video_id}.mkv',
    ]
    
    archivos = []
    for patron in patrones:
        archivos.extend(glob.glob(patron))
    
    if not archivos:
        return "Error: No se encontró el archivo descargado", 500

    # Elegir el mejor archivo (preferir mp4 para video, mp3 para audio)
    if formato == 'audio':
        archivos_audio = [f for f in archivos if f.endswith('.mp3')]
        archivo = archivos_audio[0] if archivos_audio else archivos[0]
    else:
        archivos_video = [f for f in archivos if f.endswith('.mp4')]
        archivo = archivos_video[0] if archivos_video else archivos[0]
    
    ext = archivo.split('.')[-1]
    
    # Mapear extensiones a tipos MIME
    mime_types = {
        'mp4': 'video/mp4',
        'webm': 'video/webm',
        'mkv': 'video/x-matroska',
        'mp3': 'audio/mpeg',
        'm4a': 'audio/mp4',
        'opus': 'audio/opus',
        'ogg': 'audio/ogg',
    }
    
    mimetype = mime_types.get(ext, 'application/octet-stream')
    
    def generar():
        try:
            with open(archivo, 'rb') as f:
                while True:
                    chunk = f.read(1024 * 256)  # 256KB chunks
                    if not chunk:
                        break
                    yield chunk
        finally:
            # Limpiar archivos temporales
            try:
                if os.path.exists(archivo):
                    os.remove(archivo)
                # Limpiar todos los archivos temporales del video
                for f in glob.glob(f'/tmp/{video_id}.*'):
                    if os.path.exists(f):
                        os.remove(f)
            except:
                pass

    # Crear respuesta con streaming
    response = Response(
        generar(),
        mimetype=mimetype,
        headers={
            'Content-Disposition': f'attachment; filename="{titulo}.{ext}"',
            'Content-Length': str(os.path.getsize(archivo)),
            'X-Content-Type-Options': 'nosniff',
        }
    )
    
    return response

@app.route('/health')
def health():
    """Endpoint para verificar que el servidor está funcionando"""
    cookies_existen = os.path.exists(COOKIES_PATH)
    return {
        'status': 'ok',
        'cookies': cookies_existen,
        'version': '3.0'
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"Iniciando servidor en puerto {port}")
    print(f"Cookies configuradas: {'Sí' if os.environ.get('YOUTUBE_COOKIES') else 'No'}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )
