# pylint: disable=unused-variable
# pylint: enable=too-many-lines

# ╔═════════════════════════════════════════════════════════════════════════════════════════════╗
# ║ Servicio de gestión de usuarios para proyecto de Arquitectura de Sistemas (02 - 2020)       ║
# ╠═════════════════════════════════════════════════════════════════════════════════════════════╣
# ║ Integrantes:                                                                                ║
# ║ * Lorenzo Alfaro Bravo                                                                      ║
# ║ * Flor Calla Lazo                                                                           ║
# ║ * Sebastián Toro Severino                                                                   ║
# ╚═════════════════════════════════════════════════════════════════════════════════════════════╝

# Módulos a utilizar
from db import db_wrapper
from datetime import datetime
from db.db_credentials import *
import socket, argparse, bcrypt, os, pickle
from colorama import Back, Fore, Style, init

# Inicialización para librería de colores
init()

# Función para limpiar pantalla
def clear_screen():
  os.system('cls' if os.name == 'nt' else 'clear')

# Función para reemplazar últimos caracteres en strings
def replace_last(source_string, replace_what, replace_with):
  head, _sep, tail = source_string.rpartition(replace_what)
  return head + replace_with + tail

# Constantes para combinaciones de colores y estilos (Back -> color de fondo, Fore -> color de texto)
INSTRUCTIONS_STYLE = Back.WHITE + Fore.BLACK
ERROR_STYLE = Back.RED + Fore.WHITE
WARNING_STYLE = Back.YELLOW + Fore.WHITE
INFO_STYLE = Back.BLUE + Fore.WHITE
SUCCESS_STYLE = Back.GREEN + Fore.WHITE

class Service:
  def __init__(self, host, port, name):
    self.service_title = 'Servicio de gestión de usuarios' # Título con descripción del servicio
    self.service_name = name # Nombre del servicio para reconocimiento del bus de servicios

    # Se realiza la conexión a la base de datos con las credenciales
    self.db = db_wrapper.Database(DB_HOST, DB_PORT, DB_USER, DB_PASSWD, DB_DATABASE)

    # Se genera el socket utilizando protocolo TCP
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
      self.sock.connect((host, int(port)))
      print(INSTRUCTIONS_STYLE+self.service_title+Style.RESET_ALL)
      print(SUCCESS_STYLE+'['+str(datetime.now().replace(microsecond=0))+'] Servicio conectado correctamente al bus de servicios. Host: '+str(host)+' - Puerto: '+str(port)+Style.RESET_ALL)
      # En caso de conectar exitosamente, se guarda como atributo el host y el puerto
      self.host = host
      self.port = port

      self.bus_register() # Registro del servicio en el bus de servicios

      self.run() # Inicio de la ejecución del servicio

    except Exception as error:
      print(ERROR_STYLE+'[Error] Se ha producido el siguiente error al establecer conexión con el bus de servicios:')
      print(str(error)+Style.RESET_ALL)
  
  # Registro del nombre de servicio en el bus previo a la ejecución
  def bus_register(self):
    try:
      tx_cmd = 'sinit'+self.service_name # Comando de registro de servicio ante el bus
      tx = self.generate_tx_length(len(tx_cmd)) + tx_cmd

      self.sock.send(tx.encode(encoding='UTF-8'))
      status = self.sock.recv(10000).decode('UTF-8')[10:12] # 'OK' (exitoso) o 'NK' (fallido)
      
      if status.lower() == 'ok':
        # Se ha realizado correctamente el registro del servicio con el nombre
        print(SUCCESS_STYLE+'['+str(datetime.now().replace(microsecond=0))+'] Servicio registrado correctamente en el bus de servicios con nombre "'+str(self.service_name)+'"'+Style.RESET_ALL)
    
    except Exception as error:
      print(ERROR_STYLE+'[Error] Se ha producido el siguiente error al registrar el servicio:')
      print(str(error)+Style.RESET_ALL)
      return
  
  # Método para generar el largo de la transacción (servicio + data) - Ej: 18 (int) --> 00018 (str)
  def generate_tx_length(self, tx_length):
    char_ammount = 5 # Cantidad de caracteres máximos para definir el largo de la transacción (5 según formato solicitado por el bus)
    char_left = char_ammount - len(str(tx_length)) # Espacios sobrantes para rellenar con 0 a la izquierda

    str_tx_length = ''
    for i in range(char_left):
      str_tx_length += '0'
    
    str_tx_length += str(tx_length) # String con el largo de la transacción
    
    return str_tx_length 
  
  # Método generador de la transacción con el formato correspondiente establecido en el bus
  def generate_tx(self, data):
    return self.generate_tx_length(len(self.service_name + data)) + self.service_name + data
  
  # Método para dividir la transacción recibida desde el cliente a través del bus de servicios
  def split_tx(self ,tx):
    tx_length = tx[:5] # Largo de la transacción (formato str)
    tx_service = tx[5:10] # Nombre del servicio invocado
    tx_data = tx[10:] # Datos enviados por el cliente

    return (tx_length, tx_service, tx_data)
  
  def run(self):
    # El servicio se mantiene escuchando a través del socket
    while True:
      tx = self.sock.recv(10000)

      if not tx:
        # Se cierra el servicio si no se reciben datos desde el socket
        self.sock.close()
        break

      try:
        tx = tx.decode('UTF-8')
        # Se procesa la transacción para obtener los componentes individuales
        tx_length, tx_service, tx_data = self.split_tx(tx)

        print('')
        print(INFO_STYLE+'['+str(datetime.now().replace(microsecond=0))+'] Transacción recibida desde cliente'+Style.RESET_ALL)
        print(INSTRUCTIONS_STYLE+'\t- Largo de la transacción: ' +str(tx_length)+' ('+str(int(tx_length))+')'+Style.RESET_ALL)
        print(INSTRUCTIONS_STYLE+'\t- Servicio invocado: '+str(tx_service)+Style.RESET_ALL)
        print(INSTRUCTIONS_STYLE+'\t- Datos recibidos: '+str(tx_data)+Style.RESET_ALL)

        # Se revisa el número de operación recibido desde el cliente
        try:
          client_data = eval(tx_data)

          # Se verifica la opción de transacción enviada por el cliente
          tx_option = client_data['tx_option']

          if tx_option == 0: # SOLICITUD DE MENÚ INTERNO 
            print(INSTRUCTIONS_STYLE+'\t- Funcionalidad requerida: Solicitud de menú interno'+Style.RESET_ALL)
            # Se envía el menú interno al cliente
            option_list = ['Ver lista de usuarios registrados', 
                            'Agregar nuevo usuario',
                            'Ver detalle de usuario', 
                            'Modificar usuario', 
                            'Eliminar usuario', 
                            'Volver']
            resp_data = {}
            resp_data['menu_title'] = 'Menú de gestión de usuarios'
            resp_data['menu_subtitle'] = 'Selecciona una de las opciones a continuación.'
            resp_data['menu_options'] = option_list
          
          elif tx_option == 1: # LISTA DE USUARIOS REGISTRADOS
            print(INSTRUCTIONS_STYLE+'\t- Funcionalidad requerida: Lista de usuarios registrados'+Style.RESET_ALL)
            # Se envía la lista de usuarios registrados (ordenada por apellidos)
            sql_query = '''
              SELECT rut,nombres,apellidos,email,direccion
                FROM Usuarios
                  ORDER BY apellidos ASC
            '''
            cursor = self.db.query(sql_query, None)

            # Se genera el objeto a enviar
            resp_data = {}
            resp_data['users_list'] = cursor.fetchall()
          
          elif tx_option == 2: # REGISTRO DE NUEVO USUARIO
            print(INSTRUCTIONS_STYLE+'\t- Funcionalidad requerida: Registro de nuevo usuario'+Style.RESET_ALL)

            # Se transforman los datos del usuario a registrar, obtenidos desde el cliente
            user_data = client_data['user_data']

            # Se comprueba la existencia del usuario en la base de datos según RUT o correo
            sql_query = '''
              SELECT rut
                FROM Usuarios
                  WHERE rut = %s OR email = %s
            '''
            cursor = self.db.query(sql_query, (user_data['rut'], user_data['email']))
            reg_count = len(cursor.fetchall())

            if reg_count != 0:
              # Se notifica el error al estar registrado el usuario según el rut o email recibido
              error_msg = '[Error] El rut o correo electrónico ingresado se encuentran en uso.'
              resp_data = {'success': False, 'error_notification': error_msg}

            else:
              # Se registra el usuario con los datos entregados
              user_data['password'] = user_data['password'].decode('UTF-8')

              sql_query = '''
                INSERT INTO Usuarios (rut, nombres, apellidos, email, direccion, tipo_usuario, password)
                  VALUES (%s, %s, %s, %s, %s, %s, %s)
              '''
              self.db.query(sql_query, tuple(user_data.values()))

              # Luego de registrar, se notifica al cliente
              success_msg = 'El usuario ha sido registrado correctamente.'
              resp_data = {'success': True, 'success_notification': success_msg}
          
          elif tx_option == 3: # VER DETALLE DE USUARIO
            print(INSTRUCTIONS_STYLE+'\t- Funcionalidad requerida: Ver detalle de usuario'+Style.RESET_ALL)

            # Se obtienen los datos del usuario y las posibles mascotas asociadas según el RUT indicado
            sql_query = '''
              SELECT rut, nombres, apellidos, email, direccion, tipo_usuario
                FROM Usuarios
                  WHERE rut = %s
            '''
            cursor = self.db.query(sql_query, (client_data['rut_usuario'],))
            user_data = cursor.fetchone()

            # Se modifica el atributo tipo usuario para mostrarlo como string
            if user_data is not None:
              user_data['tipo_usuario'] = 'Veterinario' if user_data['tipo_usuario'] == 1 else 'Cliente'

            sql_query = '''
              SELECT id, nombre
                FROM Mascotas
                  WHERE rut_propietario = %s
            '''
            cursor = self.db.query(sql_query, (client_data['rut_usuario'],))
            pet_list = cursor.fetchall()

            resp_data = {}

            if user_data is None:
              resp_data['success'] = False
              resp_data['error_notification'] = 'No se ha encontrado información asociada a un usuario con el rut ingresado.'
            
            else:
              resp_data['success'] = True
              resp_data['user_data'] = user_data
              resp_data['pet_list'] = pet_list
          
          elif tx_option == 4: # MODIFICAR INFORMACIÓN DE USUARIO
            print(INSTRUCTIONS_STYLE+'\t- Funcionalidad requerida: Modificar información de usuario'+Style.RESET_ALL)

            # Se obtiene la sub-transacción
            if client_data['tx_sub_option'] == 1: # Validación de RUT y obtención de datos del usuario (en caso de que exista)
              sql_query = '''
                SELECT rut, nombres, apellidos, email, direccion, tipo_usuario
                  FROM Usuarios
                    WHERE rut = %s
              '''
              cursor = self.db.query(sql_query, (client_data['rut_usuario'],))
              user_data = cursor.fetchone()

              # Se modifica el atributo tipo usuario para mostrarlo como string
              if user_data is not None:
                user_data['tipo_usuario'] = 'Veterinario' if user_data['tipo_usuario'] == 1 else 'Cliente'
                # Se genera la respuesta (exitosa)
                resp_data = {'user_exists': True, 'user_data': user_data}
              
              else:
                # Se genera la respuesta (no encontrado)
                resp_data = {'user_exists': False}
              
            elif client_data['tx_sub_option'] == 2: # Modificación de información de usuario
              # Se genera el substring para realizar la consulta SQL (SET attr1=a, attr2=b, ...)
              query_replace_str = ''
              user_data = client_data['user_data']

              # Se verifica, en caso de que se haya decidido modificar el correo
              if 'email' in user_data.keys():
                sql_query = '''
                  SELECT COUNT(*) AS cantidad_registros
                    FROM Usuarios
                      WHERE rut != %s AND email = %s
                '''
                cursor = self.db.query(sql_query, (user_data['rut_usuario'], user_data['email']))
                cantidad_registros = cursor.fetchone()['cantidad_registros']

                if cantidad_registros != 0:
                  # El correo seleccionado para modificar ya se encuentra en uso
                  resp_data = {'mod_error': True, 'error_notification': 'El correo electrónico seleccionado ya se encuentra en uso.'}
                  # Se genera la transacción y se envía al cliente
                  tx = self.generate_tx(str(resp_data)).encode(encoding='UTF-8')

                  self.sock.send(tx)
                  continue
          

              for attr in user_data.keys():

                if attr == 'rut_usuario':
                  continue

                replace = str(attr)+' = %s, '
                query_replace_str += replace
              
              # Se reemplaza la última ',' de la cadena de atributos a reemplazar
              query_replace_str = replace_last(query_replace_str, ',', '')

              rut_usuario = user_data['rut_usuario']
              del user_data['rut_usuario']

              # Se modifica el registro del usuario
              sql_query = 'UPDATE Usuarios SET '+query_replace_str+' WHERE rut = %s'
              
              values = tuple(user_data.values())
              values += (rut_usuario,)

              self.db.query(sql_query, values)

              resp_data = {'mod_error': False, 'success_notification': 'El usuario ha sido modificado correctamente.'}
          
          elif tx_option == 5: # ELIMINACIÓN DE USUARIO
            print(INSTRUCTIONS_STYLE+'\t- Funcionalidad requerida: Eliminación de usuario'+Style.RESET_ALL)

            # Se revisa si existe algún usuario registrado con el RUT ingresado
            sql_query = '''
              SELECT COUNT(*) AS cantidad_registros
                FROM Usuarios
                  WHERE rut = %s
            '''
            cursor = self.db.query(sql_query, (client_data['rut_usuario'],))
            cantidad_registros = cursor.fetchone()['cantidad_registros']

            if cantidad_registros == 0:
              # No existe un usuario registrado con el RUT ingresado
              resp_data = {'delete_error': True, 'error_notification': 'No se ha encontrado un usuario registrado según el RUT ingresado.'}
            
            else:
              # Se elimina al usuario con el RUT asociado
              sql_query = '''
                DELETE FROM Usuarios
                  WHERE rut = %s
              '''
              self.db.query(sql_query, (client_data['rut_usuario'],))

              # Se eliminan las posibles mascotas registradas y revisiones
              sql_query = '''
                SELECT id FROM Mascotas
                  WHERE rut_propietario = %s
              '''
              cursor = self.db.query(sql_query, (client_data['rut_usuario'],))
              pet_list = cursor.fetchall()

              for pet in pet_list:
                # Se eliminan las posibles revisiones de la mascota
                sql_query = '''
                  DELETE FROM Revisiones
                    WHERE id_mascota = %s
                '''
                self.db.query(sql_query, (pet['id'],))
              
              # Finalmente se eliminan las mascotas asociadas al usuario eliminado
              sql_query = '''
                DELETE FROM Mascotas
                  WHERE rut_propietario = %s
              '''
              self.db.query(sql_query, (client_data['rut_usuario'],))

              resp_data = {'delete_error': False, 'success_notification': 'El usuario seleccionado ha sido eliminado correctamente.'}
            
        except Exception as error:
          print(ERROR_STYLE+error+Style.RESET_ALL)
          # Se genera el error y se envía al cliente
          resp_data = {'internal_error': True, 'error_notification': str(error)}
        
        # Se genera la transacción y se envía al cliente
        tx = self.generate_tx(str(resp_data)).encode(encoding='UTF-8')

        self.sock.send(tx)
      
      except Exception as error:
        # Se notifica el error al cliente y se imprime en el servicio
        print(ERROR_STYLE+'[Error] Se ha producido el siguiente error al procesar la transacción:')
        print(str(error)+Style.RESET_ALL)
        error_msg = '[Error] Se ha producido el siguiente error al procesar la transacción:\n'+str(error)
        self.sock.send(self.generate_tx(error_msg).encode(encoding='UTF-8'))

if __name__ == '__main__':
  # Configuración de argumentos solicitados al momento de ejecutar el comando en la terminal
  parser = argparse.ArgumentParser()
  parser.add_argument('host', 
                      help='IP del host donde se encuentra enlazado el bus de servicios.'
                      )
  parser.add_argument('port', 
                      help='Número del puerto donde se encuentra enlazado el bus de servicios. (Valor numérico)', 
                      type=int
                      )
  parser.add_argument('service_name', 
                      help='Nombre del servicio a registrar en el bus de servicios (5 caracteres).'
                      )
  args = parser.parse_args()

  # Se obtienen los valores de host, puerto y nombre especificados en el comando de la terminal
  host = args.host
  port = args.port
  service_name = args.service_name

  if len(service_name) != 5:
    # Se notifica el error y se termina la ejecución
    print(ERROR_STYLE+'[Error] El nombre del servicio debe ser de 5 caracteres. (Formato del bus de servicios)'+Style.RESET_ALL)
    exit()
  
  clear_screen()
  # Se instancia el objeto de la clase servicio
  service = Service(host, port, service_name)