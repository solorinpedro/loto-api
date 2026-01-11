from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import datetime
import pytz

app = Flask(__name__)
CORS(app) # Permite que tu App Android se conecte sin bloqueos

# --- BASE DE DATOS DE DEFINICIONES (Integrada para evitar errores de archivos) ---
# Aquí definimos qué buscamos en la web y cómo lo pintamos en la App
LOTERIAS_CONFIG = [
    # LEIDSA
    {"id": "leidsa_pale", "nombre": "Quiniela Palé", "empresa": "Leidsa", "claves": ["Quiniela", "Palé"], "color": "#D32F2F", "cant": 3},
    {"id": "leidsa_loto", "nombre": "Loto - Más", "empresa": "Leidsa", "claves": ["Loto", "Más", "Súper"], "color": "#C62828", "cant": 8},
    {"id": "leidsa_pool", "nombre": "Loto Pool", "empresa": "Leidsa", "claves": ["Loto", "Pool"], "color": "#B71C1C", "cant": 5},
    {"id": "leidsa_kino", "nombre": "Super Kino TV", "empresa": "Leidsa", "claves": ["Kino"], "color": "#D32F2F", "cant": 20},
    {"id": "leidsa_pega3", "nombre": "Pega 3 Más", "empresa": "Leidsa", "claves": ["Pega", "3"], "color": "#E53935", "cant": 3},
    
    # NACIONAL
    {"id": "nacional_gana", "nombre": "Gana Más", "empresa": "Nacional", "claves": ["Gana", "Más"], "color": "#1976D2", "cant": 3},
    {"id": "nacional_noche", "nombre": "Lotería Nacional", "empresa": "Nacional", "claves": ["Lotería", "Nacional"], "color": "#1565C0", "cant": 3},
    {"id": "juega_pega", "nombre": "Juega + Pega +", "empresa": "Nacional", "claves": ["Juega", "Pega"], "color": "#1E88E5", "cant": 5},

    # REAL
    {"id": "real_quiniela", "nombre": "Quiniela Real", "empresa": "Real", "claves": ["Quiniela", "Real"], "color": "#FFD700", "cant": 3},
    {"id": "real_loto", "nombre": "Loto Real", "empresa": "Real", "claves": ["Loto", "Real"], "color": "#FFC107", "cant": 6},

    # LOTEKA
    {"id": "loteka_quiniela", "nombre": "Quiniela Loteka", "empresa": "Loteka", "claves": ["Quiniela", "Loteka"], "color": "#7B1FA2", "cant": 3},
    {"id": "loteka_mega", "nombre": "MegaChance", "empresa": "Loteka", "claves": ["MegaChance"], "color": "#8E24AA", "cant": 5},
    {"id": "loteka_toca", "nombre": "Toca 3", "empresa": "Loteka", "claves": ["Toca", "3"], "color": "#9C27B0", "cant": 3},

    # OTRAS
    {"id": "primera_12", "nombre": "La Primera (12PM)", "empresa": "La Primera", "claves": ["Primera", "12:00"], "color": "#2E7D32", "cant": 3},
    {"id": "primera_08", "nombre": "La Primera (8PM)", "empresa": "La Primera", "claves": ["Primera", "8:00"], "color": "#388E3C", "cant": 3},
    {"id": "suerte_12", "nombre": "La Suerte (12PM)", "empresa": "La Suerte", "claves": ["Suerte", "12:30"], "color": "#009688", "cant": 3},
    {"id": "lotedom", "nombre": "Quiniela LoteDom", "empresa": "LoteDom", "claves": ["LoteDom"], "color": "#00796B", "cant": 3},
    {"id": "anguila_ma", "nombre": "Anguila (Mañana)", "empresa": "Anguila", "claves": ["Anguila", "Mañana"], "color": "#F57C00", "cant": 3},
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def scrapear_portada():
    """Descarga la portada de loteriasdominicanas.com una sola vez"""
    url = "https://loteriasdominicanas.com/"
    datos_crudos = {}
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            bloques = soup.select(".game-block")
            for block in bloques:
                # Extraer Título
                header = block.select_one(".header a")
                if not header: continue
                titulo = header.text.strip().lower()

                # Extraer Bolas
                bolas = [b.text.strip() for b in block.select(".score") if b.text.strip().isdigit()]
                if bolas:
                    datos_crudos[titulo] = bolas
    except Exception as e:
        print(f"Error scraping: {e}")
    return datos_crudos

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "API Online", "rutas": "/api/loterias"})

@app.route('/api/loterias', methods=['GET'])
def obtener_loterias():
    # 1. Obtenemos todos los datos de la web
    datos_web = scrapear_portada()
    resultados = []

    # 2. Cruzamos los datos web con nuestra configuración
    for config in LOTERIAS_CONFIG:
        numeros_encontrados = []
        
        # Buscamos coincidencias de palabras clave
        for titulo_web, bolas in datos_web.items():
            # Si TODAS las palabras clave (ej: "Loto", "Pool") están en el título web
            if all(clave.lower() in titulo_web for clave in config["claves"]):
                numeros_encontrados = bolas
                break
        
        # 3. Formateo y Relleno
        cant = config["cant"]
        if not numeros_encontrados:
            numeros_encontrados = ["--"] * cant
        else:
            # Recortar si sobran
            if len(numeros_encontrados) > cant:
                numeros_encontrados = numeros_encontrados[:cant]
            # Rellenar si faltan
            while len(numeros_encontrados) < cant:
                numeros_encontrados.append("--")

        resultados.append({
            "id": config["id"],
            "nombre": config["nombre"],
            "tanda": config["empresa"], # Usamos esto como subtitulo
            "numeros": numeros_encontrados,
            "color": config["color"]
        })

    # Fecha actual en RD
    tz = pytz.timezone('America/Santo_Domingo')
    fecha_hoy = datetime.datetime.now(tz).strftime("%d/%m/%Y %I:%M %p")

    return jsonify({
        "meta": {
            "fecha_actualizacion": fecha_hoy,
            "autor": "AbueloLoto API"
        },
        "loterias": resultados
    })

# Necesario para Vercel
if __name__ == '__main__':
    app.run(debug=True)