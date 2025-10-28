"""
Script de pruebas para la API de Notificaciones
Ejecutar: python test_api.py
"""

import requests
import json
from datetime import datetime

# Configuración
API_URL = "http://localhost:8000"  # Cambiar a tu URL de Render cuando despliegues
# API_URL = "https://rapido-ochoa-notificaciones.onrender.com"

def print_titulo(titulo):
    print("\n" + "="*60)
    print(f"  {titulo}")
    print("="*60)

def print_resultado(nombre, resultado):
    print(f"\n✅ {nombre}")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

def print_error(nombre, error):
    print(f"\n❌ {nombre}")
    print(f"Error: {error}")

def test_health():
    """Test 1: Verificar que la API esté funcionando"""
    print_titulo("TEST 1: Health Check")
    try:
        response = requests.get(f"{API_URL}/api/health")
        if response.status_code == 200:
            print_resultado("API funcionando correctamente", response.json())
            return True
        else:
            print_error("Health check falló", f"Status {response.status_code}")
            return False
    except Exception as e:
        print_error("No se pudo conectar a la API", str(e))
        return False

def test_suscribir():
    """Test 2: Suscribir una guía"""
    print_titulo("TEST 2: Suscribir Guía a Notificaciones")
    
    # Datos de prueba
    data = {
        "numero_guia": "E121101188",
        "token_fcm": "token_prueba_12345",  # Token de prueba
        "telefono": "+573001234567"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/suscribir",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print_resultado("Suscripción creada", response.json())
            return True
        else:
            print_error("Suscripción falló", f"Status {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print_error("Error al suscribir", str(e))
        return False

def test_consultar_suscripcion():
    """Test 3: Consultar estado de suscripción"""
    print_titulo("TEST 3: Consultar Estado de Suscripción")
    
    numero_guia = "E121101188"
    
    try:
        response = requests.get(f"{API_URL}/api/suscripcion/{numero_guia}")
        
        if response.status_code == 200:
            print_resultado("Suscripción encontrada", response.json())
            return True
        elif response.status_code == 404:
            print("⚠️ No se encontró suscripción activa para esta guía")
            return False
        else:
            print_error("Consulta falló", f"Status {response.status_code}")
            return False
    except Exception as e:
        print_error("Error al consultar", str(e))
        return False

def test_estadisticas():
    """Test 4: Ver estadísticas del sistema"""
    print_titulo("TEST 4: Estadísticas del Sistema")
    
    try:
        response = requests.get(f"{API_URL}/api/stats")
        
        if response.status_code == 200:
            print_resultado("Estadísticas obtenidas", response.json())
            return True
        else:
            print_error("Estadísticas fallaron", f"Status {response.status_code}")
            return False
    except Exception as e:
        print_error("Error al obtener estadísticas", str(e))
        return False

def test_cancelar_suscripcion():
    """Test 5: Cancelar suscripción"""
    print_titulo("TEST 5: Cancelar Suscripción")
    
    numero_guia = "E121101188"
    
    respuesta = input("\n¿Deseas cancelar la suscripción de prueba? (s/n): ")
    if respuesta.lower() != 's':
        print("⏭️ Test omitido")
        return True
    
    try:
        response = requests.delete(f"{API_URL}/api/suscripcion/{numero_guia}")
        
        if response.status_code == 200:
            print_resultado("Suscripción cancelada", response.json())
            return True
        elif response.status_code == 404:
            print("⚠️ No se encontró suscripción activa para cancelar")
            return False
        else:
            print_error("Cancelación falló", f"Status {response.status_code}")
            return False
    except Exception as e:
        print_error("Error al cancelar", str(e))
        return False

def main():
    """Ejecutar todos los tests"""
    print("\n" + "🚀"*30)
    print("   TEST SUITE - API DE NOTIFICACIONES RÁPIDO OCHOA")
    print("🚀"*30)
    print(f"\nAPI URL: {API_URL}")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ejecutar tests
    resultados = []
    
    resultados.append(("Health Check", test_health()))
    
    if resultados[0][1]:  # Solo continuar si la API está funcionando
        resultados.append(("Suscribir Guía", test_suscribir()))
        resultados.append(("Consultar Suscripción", test_consultar_suscripcion()))
        resultados.append(("Estadísticas", test_estadisticas()))
        resultados.append(("Cancelar Suscripción", test_cancelar_suscripcion()))
    
    # Resumen
    print_titulo("RESUMEN DE PRUEBAS")
    exitos = sum(1 for _, resultado in resultados if resultado)
    total = len(resultados)
    
    for nombre, resultado in resultados:
        emoji = "✅" if resultado else "❌"
        print(f"{emoji} {nombre}")
    
    print(f"\nResultado: {exitos}/{total} pruebas exitosas")
    print(f"Porcentaje: {(exitos/total)*100:.1f}%\n")
    
    if exitos == total:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa los logs arriba.")

if __name__ == "__main__":
    main()