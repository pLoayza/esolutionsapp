import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, simpledialog
import requests
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import threading
import base64
import os
import json
import sys

# Variable global para almacenar el token
token_global = None

# Función para obtener el token mediante Selenium
# Función para obtener el token mediante Selenium
def obtener_token():
    print("Ejecutando script para obtener el token...")

    # Solicitar credenciales al usuario
    username = simpledialog.askstring("Usuario", "Por favor, ingresa tu nombre de usuario:")
    if not username:
        print("Error: No se ingresó un usuario.")
        return None

    password = simpledialog.askstring("Contraseña", "Por favor, ingresa tu contraseña:", show="*")
    if not password:
        print("Error: No se ingresó una contraseña.")
        return None

    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-insecure-localhost")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    seleniumwire_options = {'request_filter': lambda req: "15282" in req.url}
    driver = webdriver.Chrome(
        chrome_options=chrome_options,
        seleniumwire_options=seleniumwire_options
    )
    token = None

    try:
        wait = WebDriverWait(driver, 15)
        driver.get("https://sucalcodelco.com/sign-in")

        # Rellenar los campos de usuario y contraseña con los valores ingresados
        username_field = wait.until(EC.visibility_of_element_located((By.ID, "usuario")))
        username_field.send_keys(username)

        password_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input.p-password-input")))
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)
        time.sleep(5)

        # Navegar y capturar el token
        empresa_url = "https://sucalcodelco.com/v2/empresas/ficha-consulta/ver-ficha/ZDU0ZjVmNWRzNGZ0cnQ1NzU0Mnx8MTUyODIkJGQ1NGY1ZjVkczRmdHJ0NTc1NDI"
        driver.get(empresa_url)
        time.sleep(10)

        for request in driver.requests:
            if request.response and "15282" in request.url:
                token = request.headers.get("Authorization")
                print(f"Token obtenido: {token}")
                break
    except Exception as e:
        print(f"Error obteniendo el token: {e}")
    finally:
        driver.quit()

    return token


# Función para obtener contratos
def obtener_contratos(token, id_empresa, output):
    """
    Realiza la solicitud HTTP para obtener los contratos acreditados de una empresa.
    """
    global token_global
    url_contratos = f"https://sucal-prod-cl-api.sucalcodelco.com/v1/acreditacion-empresas/contratos/obtener-vinculo-comercial/{id_empresa}"
    headers = {"Authorization": token, "Accept": "application/json"}

    try:
        response = requests.get(url_contratos, headers=headers)
        if response.status_code == 200:
            data = response.json().get('data', [])
            contratos_acreditados = [c for c in data if c.get('estado') == 'ACREDITADO']

            if not contratos_acreditados:
                output.insert(tk.END, "No se encontraron contratos con estado ACREDITADO.\n")
            else:
                output.insert(tk.END, f"Total de contratos acreditados encontrados: {len(contratos_acreditados)}\n\n")

                for contrato in contratos_acreditados:
                    id_contrato = contrato.get('id', 'N/A')
                    numero_contrato = contrato.get('numeroContrato', 'N/A')
                    descripcion_servicio = contrato.get('descripcionServicio', 'N/A')
                    fecha_inicio = contrato.get('fechaInicio', 'N/A')
                    fecha_termino = contrato.get('fechaTermino', 'N/A')
                    estado = contrato.get('estado', 'N/A')
                    centro_trabajo = contrato.get('centroTrabajo', {}).get('nombre', 'N/A')

                    # Segunda solicitud para obtener la dotación real de personas
                    url_empleados = "https://sucal-prod-cl-api.sucalcodelco.com/v1/acreditacion-personas/empleados/obtener-empleados-por-id-contrato"
                    payload = {
                        "idContrato": id_contrato,
                        "incluirTotal": True,
                        "skip": 0,
                        "take": 2500,
                        "buscarHijos": False
                    }
                    headers_post = {
                        "Authorization": token,
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }

                    try:
                        response_empleados = requests.post(url_empleados, json=payload, headers=headers_post)
                        if response_empleados.status_code == 200:
                            empleados_data = response_empleados.json().get("data", {}).get("empleados", [])

                            # Filtrar empleados que cumplan las condiciones
                            empleados_habilitados = [
                                empleado for empleado in empleados_data
                                if empleado.get('estado') == 'ACREDITADO' and
                                any(credencial.get('estado') == 'HABILITADA' for credencial in empleado.get('credenciales', []))
                            ]

                            total_empleados_habilitados = len(empleados_habilitados)
                        else:
                            total_empleados_habilitados = "Error al obtener la dotación"
                    except Exception as e:
                        total_empleados_habilitados = f"Error: {str(e)}"

                    # Agregar la información al output
                    output.insert(tk.END, f"ID Contrato: {id_contrato}\n")
                    output.insert(tk.END, f"Número de Contrato: {numero_contrato}\n")
                    output.insert(tk.END, f"Descripción del Servicio: {descripcion_servicio}\n")
                    output.insert(tk.END, f"Fecha de Inicio: {fecha_inicio}\n")
                    output.insert(tk.END, f"Fecha de Término: {fecha_termino}\n")
                    output.insert(tk.END, f"Estado: {estado}\n")
                    output.insert(tk.END, f"Centro de Trabajo: {centro_trabajo}\n")
                    output.insert(tk.END, f"Dotación de Personas Habilitadas: {total_empleados_habilitados}\n")
                    output.insert(tk.END, "-" * 50 + "\n")

        elif response.status_code == 401:
            output.insert(tk.END, f"Token no autorizado: {token}\n")
            output.insert(tk.END, "Por favor, reinicia la aplicación para generar un nuevo token.\n")
        else:
            output.insert(tk.END, f"Error en la solicitud: {response.status_code}\n")
    except Exception as e:
        output.insert(tk.END, f"Error procesando los contratos: {e}\n")

# Función para descargar exámenes
# Función para descargar exámenes
def descargar_examenes(token, id_contrato, ruts, output, nombre_carpeta):
    """
    Descarga exámenes médicos asociados a una lista de RUTs para un contrato específico.
    """
    output.insert(tk.END, f"Iniciando descarga de exámenes para contrato {id_contrato}...\n")
    
    # API para obtener empleados
    url_empleados = "https://sucal-prod-cl-api.sucalcodelco.com/v1/acreditacion-personas/empleados/obtener-empleados-por-id-contrato"
    url_base_documentos = "https://sucal-prod-cl-api.sucalcodelco.com/v1/acreditacion-personas/empleados/obtener-documentos-acreditacion/"
    url_base_firma = "https://sucal-prod-cl-api.sucalcodelco.com/v1/acreditacion-comunes/documentos/url-signed/"
    
    # Crear la carpeta para guardar los documentos si no existe
    if not os.path.exists(nombre_carpeta):
        os.makedirs(nombre_carpeta)
    try:
        id_contrato = int(id_contrato)  # Conversión explícita a entero
    except ValueError:
        output.insert(tk.END, "Error: El ID del contrato debe ser un número válido.\n")
        return
    # Payload para obtener empleados del contrato
    payload = {
    "idContrato": id_contrato,
    "incluirTotal": True,
    "skip": 0,
    "take": 2500,
    "buscarHijos": False
}
    headers = {
    "Authorization": token,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

    try:
        response = requests.post(url_empleados, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            empleados = data.get("data", {}).get("empleados", [])
            
            # Filtrar empleados acreditados cuyos RUTs están en la lista
            empleados_acreditados = [
                emp for emp in empleados 
                if emp.get("estado") == "ACREDITADO" and emp["persona"]["identificacion"] in ruts
            ]

            output.insert(tk.END, f"Se encontraron {len(empleados_acreditados)} empleados acreditados con RUTs filtrados.\n")

            for emp in empleados_acreditados:
                emp_id = emp["id"]
                nombre_completo = f"{emp['persona']['apellidoPaterno']} {emp['persona']['apellidoMaterno']} {emp['persona']['identificacion']}"
                url_documentos = f"{url_base_documentos}{emp_id}"
                
                # Solicitar documentos del empleado
                response_docs = requests.get(url_documentos, headers=headers)
                
                if response_docs.status_code == 200:
                    documentos = response_docs.json().get("data", {}).get("documentos", [])
                    
                    # Filtrar documentos de examen médico
                    for documento in documentos:
                        tipo_documento = documento.get("documento", {}).get("tipoDocumento", {}).get("codigo")
                        if tipo_documento == "CertAprobExamSal":
                            ruta_repositorio = documento.get("documento", {}).get("rutaRepositorio")
                            
                            if ruta_repositorio:
                                # Codificar la URL en Base64
                                token_firma = base64.urlsafe_b64encode(ruta_repositorio.encode()).decode()
                                url_firma = f"{url_base_firma}{token_firma}"
                                
                                # Solicitar enlace firmado
                                response_firma = requests.get(url_firma, headers=headers)
                                
                                if response_firma.status_code == 200:
                                    enlace_firmado = response_firma.json().get("data")
                                    
                                    if enlace_firmado:
                                        # Descargar el documento firmado
                                        response_doc = requests.get(enlace_firmado)
                                        
                                        if response_doc.status_code == 200:
                                            # Guardar el archivo en la carpeta con el formato "ApellidoPaterno ApellidoMaterno RUT.pdf"
                                            nombre_archivo = os.path.join(nombre_carpeta, f"{nombre_completo}.pdf")
                                            with open(nombre_archivo, "wb") as file:
                                                file.write(response_doc.content)
                                            output.insert(tk.END, f"Documento guardado: {nombre_archivo}\n")
                                        else:
                                            output.insert(tk.END, f"Error al descargar el documento: {response_doc.status_code}\n")
                                else:
                                    output.insert(tk.END, f"Error al obtener enlace firmado: {response_firma.status_code}\n")
                else:
                    output.insert(tk.END, f"Error al obtener documentos para empleado ID {emp_id}: {response_docs.status_code}\n")
        elif response.status_code == 400:
            # Capturar detalles del error 400
            error_message = response.json() if response.headers.get("Content-Type") == "application/json" else response.text
            output.insert(tk.END, f"Error en la solicitud de empleados (400): {error_message}\n")
        else:
            output.insert(tk.END, f"Error en la solicitud de empleados: {response.status_code}\n")
    except Exception as e:
        output.insert(tk.END, f"Error procesando la descarga de exámenes: {e}\n")

# Función para actualizar las empresas en el combobox
def actualizar_empresas(filtered_empresas):
    empresa_combobox['values'] = [f"{id_empresa} - {nombre}" for id_empresa, nombre in filtered_empresas.items()]

# Función para filtrar empresas
def filtrar_empresas(event):
    filtro = filtro_entry.get().strip().lower()
    filtered_empresas = {id_empresa: nombre for id_empresa, nombre in empresas.items() if filtro in nombre.lower()}
    actualizar_empresas(filtered_empresas)


def consultar_contratos():
    """
    Función conectada al botón 'Consultar Contratos'.
    Obtiene la empresa seleccionada, valida su ID, y llama a 'obtener_contratos'.
    """
    global token_global
    id_empresa = empresa_id_var.get()
    if not id_empresa:
        messagebox.showwarning("Advertencia", "Selecciona una empresa primero.")
    elif not token_global:
        messagebox.showerror("Error", "El token no está disponible. Intenta reiniciar la aplicación.")
    else:
        output.insert(tk.END, f"Consultando contratos para la empresa ID: {id_empresa}\n")
        obtener_contratos(token_global, id_empresa, output)

# Función para manejar la selección de empresa
def seleccionar_empresa():
    seleccion = empresa_combobox.get()
    if seleccion:
        id_empresa, nombre = seleccion.split(" - ", 1)
        empresa_id_var.set(id_empresa)
        empresa_nombre_var.set(nombre)
        output.delete(1.0, tk.END)
        output.insert(tk.END, f"Empresa seleccionada:\nID: {id_empresa}\nNombre: {nombre}\n")
    else:
        messagebox.showwarning("Advertencia", "Por favor, selecciona una empresa.")

def descargar_examenes_popup(token, output):
    """
    Solicita la ID del contrato y la lista de RUTs mediante un popup y descarga los exámenes.
    """
    # Solicitar la ID del contrato
    id_contrato = simpledialog.askstring("ID del Contrato", "Por favor, ingresa la ID del contrato:")
    if not id_contrato:
        messagebox.showwarning("Advertencia", "No se ingresó una ID de contrato. Operación cancelada.")
        return

    # Solicitar la lista de RUTs
    lista_ruts_input = simpledialog.askstring("Lista de RUTs", "Por favor, ingresa la lista de RUTs separados por comas:")
    if not lista_ruts_input:
        messagebox.showwarning("Advertencia", "No se ingresaron RUTs. Operación cancelada.")
        return

    # Convertir la lista de RUTs ingresada en un formato adecuado
    lista_ruts = [rut.strip() for rut in lista_ruts_input.split(",")]

    # Solicitar la carpeta de destino
    nombre_carpeta = simpledialog.askstring("Carpeta de Descarga", "Ingresa el nombre de la carpeta para guardar los exámenes:")
    if not nombre_carpeta:
        nombre_carpeta = "examenes"  # Nombre por defecto si no se especifica

    # Iniciar la descarga de exámenes
    output.insert(tk.END, f"Descargando exámenes para contrato {id_contrato} y RUTs: {', '.join(lista_ruts)}...\n")
    descargar_examenes(token, id_contrato, lista_ruts, output, nombre_carpeta)



# Interfaz gráfica principal
def main():
    global token_global, filtro_entry, empresa_combobox, output, empresa_id_var, empresa_nombre_var, empresas

    # Generar el token al inicio
    token_global = obtener_token()
    if not token_global:
        messagebox.showerror("Error", "No se pudo generar el token. Verifica las credenciales.")
    try:
        with open("empresas.json", "r", encoding="utf-8") as file:
            empresas = json.load(file)
    except FileNotFoundError:
        empresas = {}
        messagebox.showerror("Error", "No se encontró el archivo 'empresas.json'.")
    except json.JSONDecodeError:
        empresas = {}
        messagebox.showerror("Error", "El archivo 'empresas.json' tiene un formato inválido.")

    root = tk.Tk()
    root.title("Sistema de Consultas y Descargas")
    root.geometry("800x600")

    # Frame para opciones
    opciones_frame = tk.Frame(root)
    opciones_frame.pack(pady=20, fill="x")

    ttk.Label(opciones_frame, text="Filtrar Empresas:").pack(side="left", padx=5)
    filtro_entry = tk.Entry(opciones_frame, width=40)
    filtro_entry.pack(side="left", padx=5)
    filtro_entry.bind("<KeyRelease>", filtrar_empresas)

    ttk.Label(opciones_frame, text="Seleccionar Empresa:").pack(side="left", padx=5)
    empresa_combobox = ttk.Combobox(opciones_frame, width=50, state="readonly")
    empresa_combobox.pack(side="left", padx=5)

    tk.Button(opciones_frame, text="Seleccionar", command=seleccionar_empresa).pack(side="left", padx=5)

    # Botón para consultar contratos de la empresa seleccionada
    tk.Button(opciones_frame, text="Consultar Contratos", command=consultar_contratos).pack(side="left", padx=5)

    # Frame para mostrar información seleccionada
    datos_frame = tk.Frame(root)
    datos_frame.pack(pady=20, fill="x")

    ttk.Label(datos_frame, text="ID Empresa:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    empresa_id_var = tk.StringVar()
    ttk.Label(datos_frame, textvariable=empresa_id_var).grid(row=0, column=1, padx=5, pady=5, sticky="w")

    ttk.Label(datos_frame, text="Nombre Empresa:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    empresa_nombre_var = tk.StringVar()
    ttk.Label(datos_frame, textvariable=empresa_nombre_var).grid(row=1, column=1, padx=5, pady=5, sticky="w")


    tk.Button(opciones_frame, text="Descargar Exámenes", command=lambda: descargar_examenes_popup(token_global, output)).pack(side="left", padx=5)
    # Área de texto para mostrar resultados
    output = tk.Text(root, height=20, width=100)
    output.pack(pady=10)

    # Inicializar combobox con todas las empresas
    actualizar_empresas(empresas)
    

    root.mainloop()

if __name__ == "__main__":
    main()