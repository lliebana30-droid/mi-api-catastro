from fastapi import FastAPI, HTTPException
import requests
import xmltodict

app = FastAPI(title="Puente Catastro")

@app.get("/consultar")
def consultar_catastro(tipo_via: str, nombre_via: str, numero: str, municipio: str = "MADRID", provincia: str = "MADRID"):
    
    # Usamos la IP directa del Catastro de España para saltar el bloqueo de DNS
    URL_CATASTRO = "https://94.142.231.111/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/OVCConsultaCompleta"
        
    payload = {
        'Provincia': provincia,
        'Municipio': municipio,
        'TipoVia': tipo_via,
        'NombreVia': nombre_via,
        'Numero': numero,
        'Bloque': '', 'Escalera': '', 'Planta': '', 'Puerta': ''
    }
    
    # Combinamos el Host obligatorio y el User-Agent en el mismo diccionario de cabeceras
    headers = {
        'Host': 'ovc.catastro.hacienda.gob.es',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
    }
    
    try:
        # Hacemos la llamada añadiendo las cabeceras completas y desactivando la verificación SSL por usar IP
        response = requests.get(URL_CATASTRO, params=payload, headers=headers, verify=False, timeout=15)
            
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Error del Catastro: {response.status_code}")
            
        datos_dict = xmltodict.parse(response.text)
        
        # El Catastro a veces devuelve 'consulta_coordenadas' o 'consulta_coordenadas_ni' dependiendo de la respuesta
        # Para que tu código no falle si cambia el nombre de la etiqueta raíz, lo controlamos aquí:
        raiz = list(datos_dict.keys())[0] if datos_dict else None
        
        if not raiz or 'loct' not in datos_dict[raiz]:
            return {"status": "error", "message": "Dirección no encontrada en el Catastro."}
            
        coordenadas = datos_dict[raiz]
        if 'lrc' not in coordenadas['loct']:
            return {"status": "error", "message": "No se pudieron extraer los datos catastrales."}
            
        ref_catastral = f"{coordenadas['loct']['lrc'].get('pc1', '')}{coordenadas['loct']['lrc'].get('pc2', '')}"
        datos_bienes = coordenadas['loct'].get('bi', {})
        
        return {
            "status": "success",
            "referencia_catastral": ref_catastral,
            "datos_inmueble": datos_bienes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
