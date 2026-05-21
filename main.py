import os
import glob
import yt_dlp
from flask import Flask, render_template_string, request, Response, stream_with_context

app = Flask(__name__)
COOKIES_PATH = 'cookies.txt'

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
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
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
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
            margin-bottom: 20px;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
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
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        button:active {
            transform: translateY(0);
        }
        .info {
            margin-top: 20px;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 10px;
            font-size: 12px;
            color: #666;
            text-align: center;
        }
        .error {
            color: #d32f2f;
            background: #ffebee;
            padding: 10px;
            border-radius: 5px;
            margin-top: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎥 Descargador YouTube</h1>
        <p class="subtitle">Descarga videos fácilmente</p>
        <form action="/descargar" method="GET" onsubmit="return validarURL()">
            <input type="text" name="url" id="url" placeholder="Pega el enlace de YouTube aquí..." required>
            <button type="submit">⬇️ Descargar Video</button>
        </form>
        <div class="info">
            ✅ Compatible con todos los dispositivos<br>
            📱 Móvil | 💻 PC | 📟 Tablet
        </div>
    </div>
    
    <script>
        function validarURL() {
            const url = document.getElementById('url').value;
            if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
                alert('Por favor, introduce una URL válida de YouTube');
                return false;
            }
            document.querySelector('button').textContent = '⏳ Procesando...';
            document.querySelector('button').disabled = true;
            return true;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def inicio():
    return render_template_string(PAGINA_HTML)

@app.route('/descargar', methods=['GET'])
def descargar():
    video_url = request.args.get('url')
    if not video_url:
        return "❌ Error: No se proporcionó una URL", 400
    
    # Validar que sea una URL de YouTube
    if 'youtube.com' not in video_url and 'youtu.be' not in video_url:
        return """
        <html><body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h2>❌ URL no válida</h2>
            <p>Por favor, introduce una URL de YouTube válida</p>
            <a href="/" style="color: #667eea;">⬅️ Volver</a>
        </body></html>
        """, 400

    # Configuración mejorada
    opciones = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best[height<=720]/best',  # Limitar a 720p para mejor compatibilidad
        'outtmpl': '/tmp/%(id)s.%(ext)s',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        },
        'socket_timeout': 30,
        'retries': 3,
    }

    if os.path.exists(COOKIES_PATH):
        opciones['cookiefile'] = COOKIES_PATH
        print("✅ Cookies cargadas correctamente")

    try:
        # Informar al usuario que estamos procesando
        print(f"📥 Procesando: {video_url}")
        
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_id = info.get('id')
            titulo = info.get('title', 'video')
            # Limpiar el título para el nombre del archivo
            titulo = "".join(c for c in titulo if c.isalnum() or c in (' ', '-', '_')).rstrip()
            if not titulo:
                titulo = 'video'

        archivos = glob.glob(f'/tmp/{video_id}.*')
        if not archivos:
            return """
            <html><body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h2>❌ Error de descarga</h2>
                <p>No se pudo encontrar el archivo descargado. Intenta con otro video.</p>
                <a href="/" style="color: #667eea;">⬅️ Intentar de nuevo</a>
            </body></html>
            """, 500

        archivo = archivos[0]
        ext = os.path.splitext(archivo)[1][1:]  # Obtener extensión sin el punto
        
        def generar():
            try:
                with open(archivo, 'rb') as f:
                    while True:
                        chunk = f.read(8192)  # Chunks más pequeños para mejor streaming
                        if not chunk:
                            break
                        yield chunk
            finally:
                # Limpiar el archivo después de enviarlo
                if os.path.exists(archivo):
                    try:
                        os.remove(archivo)
                    except:
                        pass

        # Determinar el mimetype correcto
        mimetypes = {
            'mp4': 'video/mp4',
            'webm': 'video/webm',
            'mkv': 'video/x-matroska',
            '3gp': 'video/3gpp',
        }
        mimetype = mimetypes.get(ext, 'video/mp4')

        response = Response(
            stream_with_context(generar()),
            mimetype=mimetype
        )
        response.headers['Content-Disposition'] = f'attachment; filename="{titulo}.{ext}"'
        response.headers['Content-Type'] = mimetype
        
        print(f"✅ Video listo para descargar: {titulo}.{ext}")
        return response
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error: {error_msg}")
        
        # Mensaje de error amigable
        mensaje_error = "Error al procesar el video"
        if "Video unavailable" in error_msg:
            mensaje_error = "El video no está disponible o es privado"
        elif "Private video" in error_msg:
            mensaje_error = "Este video es privado"
        elif "sign in" in error_msg.lower():
            mensaje_error = "Se requiere autenticación para este video"
        
        return f"""
        <html><body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h2>❌ {mensaje_error}</h2>
            <p style="color: #666; font-size: 14px;">{error_msg[:200]}</p>
            <br>
            <a href="/" style="color: #667eea; text-decoration: none; padding: 10px 20px; background: #f0f0f0; border-radius: 5px;">⬅️ Volver</a>
        </body></html>
        """, 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Servidor iniciado en http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
