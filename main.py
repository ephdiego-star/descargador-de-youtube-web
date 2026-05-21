import os
import uuid
import glob
import yt_dlp
from flask import Flask, render_template_string, request, Response

app = Flask(__name__)
COOKIES_PATH = 'cookies.txt'

@app.route('/')
def inicio():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="es">
    <body>
        <h1>Descargador</h1>
        <form action="/descargar" method="GET">
            <input type="text" name="url" placeholder="Pega el link aquí" required>
            <button type="submit">Descargar</button>
        </form>
    </body>
    </html>
    """)

@app.route('/descargar', methods=['GET'])
def descargar():
    video_url = request.args.get('url')
    if not video_url: return "No URL", 400

    # Generamos un ID único para esta petición específica
    request_id = str(uuid.uuid4())
    temp_path = f'/tmp/{request_id}'

    opciones = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best[ext=mp4]/best',
        # Guardamos con un prefijo único para que nadie se cruce
        'outtmpl': f'{temp_path}.%(ext)s',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }

    if os.path.exists(COOKIES_PATH):
        opciones['cookiefile'] = COOKIES_PATH

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(video_url, download=True)
            titulo = info.get('title', 'video').replace('/', '-')
            
        # Buscamos el archivo generado usando el ID único
        archivos = glob.glob(f'{temp_path}.*')
        if not archivos: return "Error: No se encontró el archivo.", 500

        archivo = archivos[0]
        
        def generar():
            with open(archivo, 'rb') as f:
                while chunk := f.read(1024 * 256): yield chunk
            if os.path.exists(archivo): os.remove(archivo)

        return Response(generar(), mimetype='video/mp4', 
                        headers={'Content-Disposition': f'attachment; filename="{titulo}.mp4"'})
    except Exception as e:
        # Aquí verás el error real en los logs de Railway si algo falla
        print(f"ERROR DETALLADO: {str(e)}") 
        return f"Error técnico: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
