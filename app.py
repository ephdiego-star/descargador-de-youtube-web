import os
import yt_dlp
from flask import Flask, render_template_string, request, Response

app = Flask(__name__)

# Diseño visual de la página web
PAGINA_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Descargador de YouTube Web</title>
    <style>
        :root { 
            --bg: #121212; 
            --text: #ffffff; 
            --card: #1e1e1e; 
            --primary: #3b82f6; 
        }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background-color: var(--bg); 
            color: var(--text); 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            margin: 0; 
        }
        .container { 
            background: var(--card); 
            padding: 30px; 
            border-radius: 12px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.5); 
            text-align: center; 
            width: 90%; 
            max-width: 500px; 
        }
        h1 { 
            font-size: 24px; 
            margin-bottom: 20px; 
            color: var(--primary); 
        }
        input[type="text"] { 
            width: 100%; 
            padding: 12px; 
            border-radius: 8px; 
            border: 1px solid #333; 
            background: #2a2a2a; 
            color: #fff; 
            box-sizing: border-box; 
            margin-bottom: 15px; 
            font-size: 14px; 
        }
        button { 
            background: var(--primary); 
            color: white; 
            border: none; 
            padding: 12px 20px; 
            border-radius: 8px; 
            font-size: 16px; 
            font-weight: bold; 
            cursor: pointer; 
            width: 100%; 
            transition: background 0.2s; 
        }
        button:hover { 
            background: #2563eb; 
        }
        .footer { 
            margin-top: 20px; 
            font-size: 12px; 
            color: #888; 
            font-style: italic; 
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📥 Descargador Web Inteligente</h1>
        <form action="/descargar" method="GET">
            <input type="text" name="url" placeholder="Pega el enlace de YouTube aquí..." required>
            <button type="submit">Descargar Video</button>
        </form>
        <div class="footer">Funciona en Celulares, Tablets y PCs - Calidad Estándar</div>
    </div>
</body>
</html>
"""

@app.route('/')
def inicio():
    return render_template_string(PAGINA_HTML)

@app.route('/descargar')
def descargar():
    video_url = request.args.get('url')
    if not video_url:
        return "Por favor, introduce una URL válida.", 400

    # Configuración con cookies añadidas para saltar el bloqueo estricto de IP en Render
    opciones = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
    }

    # Si subiste el archivo cookies.txt, el programa lo usará automáticamente para autenticarse
    if os.path.exists('cookies.txt'):
        opciones['cookiefile'] = 'cookies.txt'

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(video_url, download=False)
            url_descarga = info.get('url')

        if not url_descarga:
            return "No se pudo obtener el enlace directo del video.", 500

        respuesta = Response(status=302)
        respuesta.headers['Location'] = url_descarga
        return respuesta

    except Exception as e:
        return f"Ocurrió un error al procesar el video: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
