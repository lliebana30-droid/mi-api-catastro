from fastapi import FastAPI, HTTPException
import requests
import xmltodict

app = FastAPI(title="Puente Catastro")

@app.get("/consultar")
def consultar_catastro(tipo_via: str, nombre_via: str, numero: str, municipio: str = "MADRID", provincia: str = "MADRID"):
        
       # URL_CATASTRO = "https://ovc.catastro.hacienda.gob.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/OVCConsultaCompleta"
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
    
    # Añadimos un User-Agent europeo estándar por seguridad
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
    }
    
    try:
       # response = requests.get(url, params=payload, headers=headers, timeout=10)

# 1. Definimos la cabecera Host justo antes de la llamada
    headers = {"Host": "ovc.catastro.hacienda.gob.es"}
    
    # 2. Hacemos la llamada añadiendo headers y verify=False
    response = requests.get(URL_CATASTRO, params=payload, headers=headers, verify=False, timeout=15)
            
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Error del Catastro: {response.status_code}")
            
        datos_dict = xmltodict.parse(response.text)
        
        if 'consulta_coordenadas' not in datos_dict:
            return {"status": "error", "message": "Dirección no encontrada."}
            
        coordenadas = datos_dict['consulta_coordenadas']
        if 'loct' not in coordenadas or 'lrc' not in coordenadas['loct']:
            return {"status": "error", "message": "No se pudieron extraer datos."}
            
        ref_catastral = f"{coordenadas['loct']['lrc'].get('pc1', '')}{coordenadas['loct']['lrc'].get('pc2', '')}"
        datos_bienes = coordenadas['loct'].get('bi', {})
        
        return {
            "status": "success",
            "referencia_catastral": ref_catastral,
            "datos_inmueble": datos_bienes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
