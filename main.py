import os
import glob
import yt_dlp
from flask import Flask, render_template_string, request, Response, stream_with_context

app = Flask(__name__)
COOKIES_PATH = os.environ.get('COOKIES_PATH', 'cookies.txt')

PAGINA_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Descargador de YouTube</title>
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
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 500px;
            width: 100%;
        }
        h1 { color: #333; margin-bottom: 10px; font-size: 28px; text-align: center; }
        .subtitle { color: #666; text-align: center; margin-bottom: 30px; font-size: 14px; }
        .alert {
            background: #fff3cd;
            border: 1px solid #ffc107;
            color: #856404;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        input[type="text"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            margin-bottom: 20px;
        }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
        }
        button:hover { transform: translateY(-2px); }
        .info { margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 10px; font-size: 12px; color: #666; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎥 Descargador YouTube</h1>
        <p class="subtitle">Descarga videos fácilmente</p>
        
        {% if not cookies_exist %}
        <div class="alert">
            ⚠️ <strong>Configuración necesaria:</strong> Las cookies de YouTube no están configuradas. 
            <a href="/configurar" style="color: #856404; font-weight: bold;">Configurar ahora</a>
        </div>
        {% endif %}
        
        <form action="/descargar" method="GET">
            <input type="text" name="url" placeholder="Pega el enlace de YouTube aquí..." required>
            <button type="submit">⬇️ Descargar Video</button>
        </form>
        <div class="info">
            ✅ Compatible con todos los dispositivos<br>
            📱 Móvil | 💻 PC | 📟 Tablet
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def inicio():
    cookies_exist = os.path.exists(COOKIES_PATH)
    return render_template_string(PAGINA_HTML, cookies_exist=cookies_exist)

@app.route('/configurar')
def configurar():
    return """
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Configurar Cookies</title>
        <style>
            body {
                font-family: 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 20px;
                padding: 40px;
                max-width: 600px;
                width: 100%;
            }
            h2 { color: #333; margin-bottom: 20px; }
            .step {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 15px;
                border-left: 4px solid #667eea;
            }
            .step h3 { color: #667eea; margin-bottom: 10px; }
            code {
                background: #e9ecef;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 14px;
            }
            .important {
                background: #fff3cd;
                border: 1px solid #ffc107;
                color: #856404;
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
            }
            a { color: #667eea; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🔧 Cómo configurar las cookies de YouTube</h2>
            
            <div class="important">
                <strong>⚠️ ¿Por qué es necesario?</strong><br>
                YouTube bloquea las descargas automáticas para prevenir bots. 
                Las cookies demuestran que eres un usuario real.
            </div>
            
            <div class="step">
                <h3>Paso 1: Instalar extensión</h3>
                <p>Instala <strong>Get cookies.txt LOCALLY</strong> en Chrome/Edge:</p>
                <a href="https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc" target="_blank">
                    🔗 Instalar extensión (Chrome Web Store)
                </a>
            </div>
            
            <div class="step">
                <h3>Paso 2: Abrir YouTube en modo incógnito</h3>
                <p>Abre una <strong>ventana de incógnito</strong> (Ctrl+Shift+N)</p>
                <p>Ve a <a href="https://www.youtube.com" target="_blank">YouTube</a> e inicia sesión</p>
            </div>
            
            <div class="step">
                <h3>Paso 3: Exportar cookies</h3>
                <p>Haz clic en el icono de la extensión y selecciona <strong>"Export"</strong></p>
                <p>Guarda el archivo como <code>cookies.txt</code></p>
            </div>
            
            <div class="step">
                <h3>Paso 4: Configurar variable de entorno</h3>
                <p>Agrega esta variable en tu plataforma (Render, Railway, etc.):</p>
                <p><code>YOUTUBE_COOKIES</code> con el contenido del archivo cookies.txt</p>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="/" style="background: #667eea; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none;">
                    ⬅️ Volver al descargador
                </a>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/debug')
def debug():
    cookies_content = os.environ.get('YOUTUBE_COOKIES')
    if not cookies_content:
        return "❌ YOUTUBE_COOKIES no está configurada como variable de entorno", 200
    
    # Verificar formato de cookies
    if not cookies_content.startswith('# Netscape HTTP Cookie File') and \
       not cookies_content.startswith('# HTTP Cookie File'):
        return "⚠️ Las cookies no tienen el formato correcto. Debe comenzar con '# Netscape HTTP Cookie File'", 200
    
    try:
        with open(COOKIES_PATH, 'w') as f:
            f.write(cookies_content)
        return f"✅ Cookies configuradas correctamente. Longitud: {len(cookies_content)} caracteres", 200
    except Exception as e:
        return f"❌ Error al escribir cookies: {str(e)}", 500

@app.route('/descargar', methods=['GET'])
def descargar():
    video_url = request.args.get('url')
    if not video_url:
        return "❌ No se proporcionó URL", 400

    # Verificar si las cookies existen
    if not os.path.exists(COOKIES_PATH):
        cookies_content = os.environ.get('YOUTUBE_COOKIES')
        if cookies_content:
            with open(COOKIES_PATH, 'w') as f:
                f.write(cookies_content)
        else:
            return """
            <html><body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h2>❌ Cookies no configuradas</h2>
                <p>Es necesario configurar las cookies de YouTube para descargar videos.</p>
                <a href="/configurar" style="color: #667eea; font-weight: bold;">🔧 Ir a configuración</a>
            </body></html>
            """, 400

    # Configuración con cookies y User-Agent
    opciones = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best[height<=720]/best',
        'outtmpl': '/tmp/%(id)s.%(ext)s',
        'cookiefile': COOKIES_PATH,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        },
        'socket_timeout': 30,
        'retries': 3,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_id = info.get('id')
            titulo = info.get('title', 'video')
            titulo = "".join(c for c in titulo if c.isalnum() or c in (' ', '-', '_')).rstrip()

        archivos = glob.glob(f'/tmp/{video_id}.*')
        if not archivos:
            return "❌ No se pudo encontrar el archivo descargado", 500

        archivo = archivos[0]
        ext = os.path.splitext(archivo)[1][1:]
        
        def generar():
            try:
                with open(archivo, 'rb') as f:
                    while chunk := f.read(8192):
                        yield chunk
            finally:
                if os.path.exists(archivo):
                    os.remove(archivo)

        return Response(
            stream_with_context(generar()),
            mimetype=f'video/{ext}',
            headers={'Content-Disposition': f'attachment; filename="{titulo}.{ext}"'}
        )
        
    except Exception as e:
        error_msg = str(e)
        
        if "Sign in to confirm you're not a bot" in error_msg:
            return """
            <html><body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h2>🤖 Detectado como bot</h2>
                <p>YouTube está bloqueando la descarga. Esto puede deberse a:</p>
                <ul style="text-align: left; display: inline-block;">
                    <li>Cookies inválidas o expiradas</li>
                    <li>Demasiadas descargas en poco tiempo</li>
                    <li>Formato de cookies incorrecto</li>
                </ul>
                <br>
                <a href="/configurar" style="color: #667eea; font-weight: bold;">🔧 Reconfigurar cookies</a>
                <br><br>
                <a href="/" style="color: #666;">⬅️ Volver</a>
            </body></html>
            """, 500
        
        return f"❌ Error: {error_msg[:200]}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Servidor iniciado en http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
