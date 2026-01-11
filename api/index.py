from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import datetime
import pytz

app = Flask(__name__)
CORS(app)

# --- CONFIGURACIÓN DE NAVEGADOR ---
# Usamos headers que parecen un Chrome real de Windows
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Referer': 'https://www.google.com/'
}

# --- CONFIGURACIÓN DE TUS LOTERÍAS ---
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

def obtener_fecha_rd():
    try:
        tz = pytz.timezone('America/Santo_Domingo')
        return datetime.datetime.now(tz).strftime("%d/%m/%Y %I:%M %p")
    except:
        return datetime.datetime.now().strftime("%d/%m/%Y")

# --- FUENTE A: LOTERIASDOMINICANAS.COM ---
def scrape_source_a():
    url = "https://loteriasdominicanas.com/"
    datos = {}
    print(f"Intentando Fuente A: {url}")
    try:
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=5)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            bloques = soup.select(".game-block")
            
            for block in bloques:
                header = block.select_one(".header a")
                if header:
                    titulo = header.text.strip().lower()
                    bolas = [b.text.strip() for b in block.select(".score") if b.text.strip().isdigit()]
                    if bolas:
                        datos[titulo] = bolas
    except Exception as e:
        print(f"Fallo Fuente A: {e}")
    return datos

# --- FUENTE B: CONECTATE.COM.DO (Respaldo) ---
def scrape_source_b():
    url = "https://www.conectate.com.do/loterias/"
    datos = {}
    print(f"Intentando Fuente B: {url}")
    try:
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=6)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Conectate tiene una estructura diferente
            # Buscamos los bloques de lotería
            bloques = soup.select(".game-block") # A veces usan clases similares o divs contenedores
            
            # Si el selector anterior falla, intentamos una busqueda mas genérica en conectate
            if not bloques:
                bloques = soup.select(".content-loterias .bloque-loteria")

            for block in bloques:
                # Titulo en conectate suele ser h3 o a
                titulo_el = block.select_one("a.title-loteria") or block.select_one("h3")
                if titulo_el:
                    titulo = titulo_el.text.strip().lower()
                    
                    # Bolas
                    bolas = []
                    spans = block.select(".bolo") # Conectate usa clase 'bolo'
                    for span in spans:
                        txt = span.text.strip()
                        if txt.isdigit():
                            bolas.append(txt)
                    
                    if bolas:
                        datos[titulo] = bolas
    except Exception as e:
        print(f"Fallo Fuente B: {e}")
    return datos

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "Online"})

@app.route('/api/loterias', methods=['GET'])
def obtener_loterias():
    # 1. Intentamos Fuente A
    datos_web = scrape_source_a()
    fuente_usada = "Fuente A (LoteriasDominicanas)"

    # 2. Si Fuente A vino vacía (posible bloqueo), activamos Fuente B
    if not datos_web:
        datos_web = scrape_source_b()
        fuente_usada = "Fuente B (Conectate)"
    
    resultados = []

    # 3. Procesamos los datos (sea cual sea la fuente que funcionó)
    for config in LOTERIAS_CONFIG:
        numeros_encontrados = []
        
        for titulo_web, bolas in datos_web.items():
            # Coincidencia difusa: Si las claves están en el título
            if all(clave.lower() in titulo_web for clave in config["claves"]):
                numeros_encontrados = bolas
                break
        
        # Relleno y seguridad
        cant = config["cant"]
        if not numeros_encontrados:
            numeros_encontrados = ["--"] * cant
        
        if len(numeros_encontrados) > cant:
            numeros_encontrados = numeros_encontrados[:cant]
        while len(numeros_encontrados) < cant:
            numeros_encontrados.append("--")

        resultados.append({
            "id": config["id"],
            "nombre": config["nombre"],
            "tanda": config["empresa"],
            "numeros": numeros_encontrados,
            "color": config["color"]
        })

    return jsonify({
        "meta": {
            "fecha_actualizacion": obtener_fecha_rd(),
            "autor": "AbueloLoto API",
            "debug_fuente": fuente_usada, # Para saber cuál funcionó
            "debug_items_encontrados": len(datos_web)
        },
        "loterias": resultados
    })

if __name__ == '__main__':
    app.run(debug=True)
