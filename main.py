import os
import glob
import yt_dlp
from flask import Flask, render_template_string, request, Response

app = Flask(__name__)
COOKIES_PATH = 'cookies.txt'

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

        input[type="text"]:focus + .input-icon {
            color: #667eea;
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
        
        <form action="/descargar" method="GET">
            <div class="input-group">
                <span class="input-icon">🔗</span>
                <input type="text" name="url" placeholder="Pega el enlace de YouTube aquí..." required>
            </div>
            <button type="submit">⬇️ Descargar Video</button>
        </form>
        
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
        
        <div class="version">v2.0 • YouTube Downloader</div>
    </div>
</body>
</html>
"""

@app.route('/')
def inicio():
    return render_template_string(PAGINA_HTML)

@app.route('/descargar', methods=['GET'])
def descargar():
    video_url = request.args.get('url')
    if not video_url: return "No URL", 400

    # Cargar cookies desde variable de entorno
    cookies_env = os.environ.get('YOUTUBE_COOKIES')
    if cookies_env:
        with open(COOKIES_PATH, 'w') as f:
            f.write(cookies_env)

    # Configuración con formato flexible
    opciones = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bv*+ba/b',
        'outtmpl': '/tmp/%(id)s.%(ext)s',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['mweb', 'android'],
            }
        },
    }

    if os.path.exists(COOKIES_PATH):
        opciones['cookiefile'] = COOKIES_PATH

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_id = info.get('id')
            titulo = info.get('title', 'video').replace('/', '-')

        archivos = glob.glob(f'/tmp/{video_id}.*')
        if not archivos: return "Error: No se encontró el archivo.", 500

        archivo = archivos[0]
        ext = archivo.split('.')[-1]
        
        def generar():
            with open(archivo, 'rb') as f:
                while chunk := f.read(1024 * 256): yield chunk
            if os.path.exists(archivo): os.remove(archivo)

        return Response(generar(), mimetype=f'video/{ext}', 
                        headers={'Content-Disposition': f'attachment; filename="{titulo}.{ext}"'})
    except Exception as e:
        return f"Error técnico: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
