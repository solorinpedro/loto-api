from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import datetime
import pytz

app = Flask(__name__)
CORS(app)

# --- CONFIGURACIÓN DE CAMUFLAJE ---
# Headers copiados de un navegador real para engañar al bloqueo
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Referer': 'https://www.google.com/',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# --- TUS LOTERÍAS ---
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

# --- FUENTE A: CONECTATE.COM.DO (PRIMERA OPCIÓN - MENOS BLOQUEOS) ---
def scrape_conectate():
    url = "https://www.conectate.com.do/loterias/"
    datos = {}
    print(f"--- Intentando CONECTATE ---")
    try:
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=8)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Buscamos bloques de lotería
            bloques = soup.select(".game-block") 
            if not bloques:
                bloques = soup.select(".content-loterias .bloque-loteria")

            for block in bloques:
                # El título suele estar en un <a> con clase title-loteria
                titulo_el = block.select_one(".game-title") or block.select_one("a.title-loteria") or block.select_one("h3")
                
                if titulo_el:
                    titulo = titulo_el.text.strip().lower()
                    
                    # Bolas: En conectate a veces son <span> con clase 'bolo' o 'score'
                    bolas = []
                    # Estrategia mixta de selectores
                    spans = block.select(".score") + block.select(".bolo")
                    
                    for span in spans:
                        txt = span.text.strip()
                        if txt.isdigit():
                            bolas.append(txt)
                    
                    # Filtramos duplicados manteniendo orden (hack de dict)
                    bolas = list(dict.fromkeys(bolas))
                    
                    if bolas:
                        datos[titulo] = bolas
    except Exception as e:
        print(f"Error Conectate: {e}")
    return datos

# --- FUENTE B: LOTERIASDOMINICANAS (RESPALDO - MEJORADA CON TU FOTO) ---
def scrape_loteriasdominicanas():
    url = "https://loteriasdominicanas.com/"
    datos = {}
    print(f"--- Intentando LOTERIASDOMINICANAS ---")
    try:
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=8)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Selector basado en tu foto: div.game-block
            bloques = soup.select("div.game-block")
            
            for block in bloques:
                header = block.select_one(".header a")
                if header:
                    titulo = header.text.strip().lower()
                    
                    # Selector basado en tu foto: div.game-scores -> span.score
                    # Usamos 'select' que busca descendientes, capturando 'score special1', 'score special2', etc.
                    contenedor_scores = block.select_one(".game-scores")
                    if contenedor_scores:
                        bolas = [b.text.strip() for b in contenedor_scores.select("span.score") if b.text.strip().isdigit()]
                        if bolas:
                            datos[titulo] = bolas
    except Exception as e:
        print(f"Error LoteriasDominicanas: {e}")
    return datos

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "Online", "msg": "API Loterias Activa"})

@app.route('/api/loterias', methods=['GET'])
def obtener_loterias():
    # ESTRATEGIA INVERTIDA:
    # 1. Probamos Conectate primero (suele bloquear menos a Vercel)
    datos_web = scrape_conectate()
    fuente = "Conectate"

    # 2. Si falló (está vacío), probamos LoteriasDominicanas con el selector de tu foto
    if not datos_web:
        datos_web = scrape_loteriasdominicanas()
        fuente = "LoteriasDominicanas"
    
    resultados = []

    # 3. Procesar datos
    for config in LOTERIAS_CONFIG:
        numeros_encontrados = []
        
        # Búsqueda difusa
        for titulo_web, bolas in datos_web.items():
            if all(clave.lower() in titulo_web for clave in config["claves"]):
                numeros_encontrados = bolas
                break
        
        # Relleno
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
            "fecha": obtener_fecha_rd(),
            "fuente_usada": fuente,
            "cantidad_datos": len(datos_web)
        },
        "loterias": resultados
    })

if __name__ == '__main__':
    app.run(debug=True)
