import os
import re
import csv
import subprocess
import time
import shlex
import shutil
import questionary
from bs4 import BeautifulSoup

def extract_links_from_html(file_path):
    """Extrae todos los enlaces de un archivo HTML, ya sea en <a> o dentro de un <p>."""
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        links = set(a['href'] for a in soup.find_all('a', href=True))
        
        # Buscar URLs dentro de etiquetas <p>
        for p in soup.find_all('p'):
            url_match = re.findall(r'https?://\S+', p.text)
            links.update(url_match)
    
    return list(links)

def extract_name_from_filename(filename):
    """Extrae solo el nombre del archivo antes del primer guion bajo."""
    return filename.split('_')[0]  # Tomar solo la primera parte antes de "_"

def extract_carnet_from_link(link):
    """Extrae el número de carnet desde el link del repositorio, con más flexibilidad."""
    match = re.search(r'(?:OLC2[_-]Proyecto1[_-]|OLC2[_-]P1[_-]|OLC2[_-]P1[_-]\w+[_-])(-?\d{6,9})', link, re.IGNORECASE)
    if match:
        return match.group(1).lstrip('-')  # Remueve cualquier guion inicial
    return "Desconocido"

def save_links_to_csv(entries, output_file):
    """Guarda los enlaces en un archivo CSV con la estructura: Nombre, Carnet, Link."""
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Nombre', 'Carnet', 'Link'])  # Escribir encabezado
            writer.writerows(entries)
        return True
    except PermissionError:
        print(f"Error: No se pudo escribir en '{output_file}'. El archivo podría estar en uso.")
        # Intentar con un nombre alternativo
        alt_file = f"{os.path.splitext(output_file)[0]}_{int(time.time())}.csv"
        try:
            with open(alt_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Nombre', 'Carnet', 'Link'])
                writer.writerows(entries)
            print(f"Se ha guardado la información en el archivo alternativo: {alt_file}")
            return True
        except:
            print(f"Error: No se pudo escribir el archivo CSV.")
            return False

def run_command_with_output(cmd):
    """Ejecuta un comando y captura su salida y código de error."""
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def clone_repo(nombre, carnet, link):
    """Clona un repositorio completo priorizando el éxito sobre la eficiencia."""
    current_dir = os.getcwd()  # Guardar el directorio actual
    commands_run = []
    error_details = None
    
    try:
        folder_name = carnet if carnet != "Desconocido" else os.path.basename(link).replace('.git', '')
        repo_path = os.path.join("repos", folder_name)
        
        print(f"Procesando: {nombre} (Carnet: {carnet})...")
        print(f"  Repositorio: {link}")
        print(f"  Carpeta destino: {repo_path}")
        
        # Eliminar la carpeta si existe para evitar conflictos
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path, ignore_errors=True)
            commands_run.append(f"rm -rf {shlex.quote(repo_path)}")
        
        # Intentar clonar directamente - método más simple y con más probabilidad de éxito
        print("  Intentando clonar el repositorio completo...")
        cmd = ["git", "clone", "--no-single-branch", link, repo_path]
        exitcode, stdout, stderr = run_command_with_output(cmd)
        commands_run.append(f"git clone --no-single-branch {shlex.quote(link)} {shlex.quote(repo_path)}")
        
        if exitcode == 0:
            print("  ✅ Clonación exitosa con el método directo.")
            return True, None, commands_run
        else:
            print(f"  ⚠️ No se pudo clonar con el método directo: {stderr}")
            error_details = f"Error al clonar directamente: {stderr}"
            
            # Método alternativo: Inicializar y fetch
            print("  Intentando método alternativo (init + fetch)...")
            
            # Crear la carpeta del repositorio
            os.makedirs(repo_path, exist_ok=True)
            commands_run.append(f"mkdir -p {shlex.quote(repo_path)}")
            
            # Cambiar al directorio del repositorio
            os.chdir(repo_path)
            commands_run.append(f"cd {shlex.quote(repo_path)}")
            
            # Inicializar el repositorio Git
            cmd = ["git", "init"]
            exitcode, stdout, stderr = run_command_with_output(cmd)
            commands_run.append("git init")
            if exitcode != 0:
                error_details += f"\nError en git init: {stderr}"
                raise Exception(error_details)
            
            # Agregar el remoto
            cmd = ["git", "remote", "add", "origin", link]
            exitcode, stdout, stderr = run_command_with_output(cmd)
            commands_run.append(f"git remote add origin {shlex.quote(link)}")
            if exitcode != 0:
                error_details += f"\nError al agregar remoto: {stderr}"
                raise Exception(error_details)
            
            # Método 1: Intentar fetch de todas las ramas
            cmd = ["git", "fetch", "--all"]
            exitcode, stdout, stderr = run_command_with_output(cmd)
            commands_run.append("git fetch --all")
            
            if exitcode == 0:
                # Intentar detectar la rama predeterminada
                cmd = ["git", "remote", "show", "origin"]
                exitcode, stdout, stderr = run_command_with_output(cmd)
                commands_run.append("git remote show origin")
                
                default_branch = "main"  # Valor predeterminado si no se puede detectar
                
                if exitcode == 0:
                    branch_match = re.search(r'HEAD branch: (.+)', stdout)
                    if branch_match:
                        default_branch = branch_match.group(1)
                        print(f"  Detectada rama predeterminada: {default_branch}")
                
                # Checkout de la rama predeterminada
                cmd = ["git", "checkout", default_branch]
                exitcode, stdout, stderr = run_command_with_output(cmd)
                commands_run.append(f"git checkout {default_branch}")
                
                if exitcode == 0:
                    print(f"  ✅ Clonación exitosa usando método alternativo (rama: {default_branch}).")
                    return True, None, commands_run
                else:
                    # Si el checkout falla, intentar listar las ramas disponibles
                    cmd = ["git", "branch", "-a"]
                    exitcode, stdout, stderr = run_command_with_output(cmd)
                    commands_run.append("git branch -a")
                    
                    if exitcode == 0 and stdout.strip():
                        # Tomar la primera rama remota disponible
                        branch_lines = [line.strip() for line in stdout.splitlines() if 'remotes/origin/' in line]
                        if branch_lines:
                            # Extraer el nombre de la rama de la primera línea
                            first_branch = branch_lines[0].split('remotes/origin/', 1)[1]
                            print(f"  Intentando con la primera rama disponible: {first_branch}")
                            
                            cmd = ["git", "checkout", "-b", first_branch, f"origin/{first_branch}"]
                            exitcode, stdout, stderr = run_command_with_output(cmd)
                            commands_run.append(f"git checkout -b {first_branch} origin/{first_branch}")
                            
                            if exitcode == 0:
                                print(f"  ✅ Clonación exitosa usando la rama: {first_branch}")
                                return True, None, commands_run
            
            error_details += "\nNo se pudo clonar con métodos alternativos"
            print("  ❌ Todos los métodos de clonación fallaron.")
            return False, error_details, commands_run
            
    except Exception as e:
        error_msg = str(e) if error_details is None else error_details
        print(f"  ❌ Error durante la clonación: {error_msg}")
        return False, error_msg, commands_run
    finally:
        # Asegurarse de volver al directorio original
        try:
            os.chdir(current_dir)
            commands_run.append(f"cd {shlex.quote(current_dir)}")
        except:
            # Si por alguna razón no podemos volver al directorio original, intentamos ir a un directorio seguro
            try:
                safe_dir = os.path.dirname(os.path.abspath(__file__))
                os.chdir(safe_dir)
                commands_run.append(f"cd {shlex.quote(safe_dir)}")
            except:
                pass
        print("  " + "-" * 50)

def filter_files_by_extension(repo_path, valid_extensions):
    """Filtra archivos dejando solo los que tienen extensiones válidas."""
    print(f"  Filtrando archivos en {repo_path}...")
    deleted_files = 0
    
    # Recorrer archivos de abajo hacia arriba para poder eliminar directorios vacíos
    for root, dirs, files in os.walk(repo_path, topdown=False):
        # Primero, eliminar archivos con extensiones no válidas
        for file in files:
            file_path = os.path.join(root, file)
            # Verificar si es un archivo .git (evitar eliminar estos)
            if ".git" in file_path.split(os.sep):
                continue
                
            ext = os.path.splitext(file)[1].lstrip('.')
            if ext not in valid_extensions:
                try:
                    os.remove(file_path)
                    deleted_files += 1
                except:
                    pass
        
        # Luego intentar eliminar directorios vacíos
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            # Evitar eliminar directorios .git
            if ".git" in dir_path.split(os.sep):
                continue
                
            try:
                # Verificar si el directorio está vacío
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
            except:
                pass
    
    print(f"  ✅ Se eliminaron {deleted_files} archivos con extensiones no válidas.")
    return deleted_files

def safe_write_file(filename, content):
    """Escribe en un archivo de forma segura, manejando errores de permisos."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return True, filename
    except PermissionError:
        # Si hay error de permisos, intentamos con un nombre alternativo
        alt_filename = f"{os.path.splitext(filename)[0]}_{int(time.time())}.txt"
        try:
            with open(alt_filename, "w", encoding="utf-8") as f:
                f.write(content)
            return True, alt_filename
        except:
            return False, None

def process_repositories_sequentially(entries, extensions):
    """Procesa los repositorios uno por uno, mostrando el resultado de cada operación."""
    # Asegurarse de que existe el directorio repos
    try:
        if os.path.exists("repos"):
            # Eliminar la carpeta repos si existe
            try:
                shutil.rmtree("repos", ignore_errors=True)
            except:
                pass
        
        os.makedirs("repos", exist_ok=True)
    except Exception as e:
        print(f"Error al preparar el directorio repos: {str(e)}")
        return
    
    # Listas para almacenar resultados
    successful_repos = []
    failed_repos = []
    
    # Procesar cada entrada
    for i, (nombre, carnet, link) in enumerate(entries, 1):
        print(f"\nRepositorio {i}/{len(entries)}")
        success, error_details, commands = clone_repo(nombre, carnet, link)
        
        if success:
            # Si la clonación fue exitosa, ahora filtramos los archivos
            folder_name = carnet if carnet != "Desconocido" else os.path.basename(link).replace('.git', '')
            repo_path = os.path.join("repos", folder_name)
            filter_files_by_extension(repo_path, extensions)
            successful_repos.append((nombre, carnet, link))
        else:
            failed_repos.append((nombre, carnet, link, error_details, commands))
    
    # Mostrar resumen
    print("\n" + "=" * 60)
    print(f"Resumen de la operación:")
    print(f"  ✅ Repositorios clonados con éxito: {len(successful_repos)}")
    print(f"  ❌ Repositorios con error: {len(failed_repos)}")
    
    # Escribir reporte de fallos
    if failed_repos:
        report_content = "REPOSITORIOS QUE NO SE PUDIERON CLONAR\n"
        report_content += "=====================================\n\n"
        
        for idx, (nombre, carnet, link, error, commands) in enumerate(failed_repos, 1):
            report_content += f"REPOSITORIO #{idx}\n"
            report_content += f"Nombre: {nombre}\n"
            report_content += f"Carnet: {carnet}\n"
            report_content += f"Link: {link}\n"
            report_content += f"Error: {error}\n\n"
            
            report_content += "Comandos para ejecutar manualmente:\n"
            report_content += "```bash\n"
            for cmd in commands:
                report_content += f"{cmd}\n"
            report_content += "```\n\n"
            report_content += "=" * 50 + "\n\n"
        
        success, filename = safe_write_file("failed_repos.txt", report_content)
        
        if success:
            print(f"\nSe ha guardado el reporte de fallos en: {filename}")
        else:
            print("\nNo se pudo guardar el reporte de fallos.")
            print("Repositorios que fallaron:")
            for i, (nombre, carnet, link, _, _) in enumerate(failed_repos[:5], 1):
                print(f"  {i}. {nombre} (Carnet: {carnet})")
            if len(failed_repos) > 5:
                print(f"  ... y {len(failed_repos) - 5} más.")

def main():
    input_folder = './entregas'
    output_file = 'links.csv'
    extensions = []  # Solo archivos .cs y .g4
    default_extensions = [".cs", ".g4"]
    
    use_defaults = questionary.confirm("¿Usar extensiones predeterminadas (.cs, .g4)?").ask()
    
    if use_defaults:
        extensions = default_extensions
    else:
        user_extensions = questionary.text("Ingrese las extensiones separadas por coma (ej. py,txt):").ask()
        extensions = [ext.strip() if ext.startswith('.') else f'.{ext.strip()}' for ext in user_extensions.split(',')]

    entries = set()
    
    try:
        if not os.path.exists(input_folder):
            print(f'Error: La carpeta {input_folder} no existe.')
            return
        
        print("Analizando archivos HTML...")
        for filename in os.listdir(input_folder):
            if filename.endswith('.html'):
                file_path = os.path.join(input_folder, filename)
                name = extract_name_from_filename(filename)
                links = extract_links_from_html(file_path)
                for link in links:
                    carnet = extract_carnet_from_link(link)
                    entries.add((name, carnet, link))
        
        if entries:
            if save_links_to_csv(list(entries), output_file):
                print(f'Se han guardado {len(entries)} enlaces en {output_file}')
                
                print(f"\nIniciando la clonación de repositorios uno por uno...")
                print(f"Solo se descargarán archivos con extensiones: {', '.join(extensions)}")
                
                start_time = time.time()
                process_repositories_sequentially(list(entries), extensions)
                end_time = time.time()
                
                print(f"\nProceso completado en {end_time - start_time:.2f} segundos.")
            else:
                print("No se pudo guardar la información en el archivo CSV.")
        else:
            print('No se encontraron enlaces en los archivos HTML.')
    except Exception as e:
        print(f"Error general en la ejecución: {str(e)}")

if __name__ == '__main__':
    main()