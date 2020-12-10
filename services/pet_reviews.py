# pylint: disable=unused-variable
# pylint: enable=too-many-lines

# ╔═════════════════════════════════════════════════════════════════════════════════════════════╗
# ║ Servicio de revisiones de mascotas para proyecto de Arquitectura de Sistemas (02 - 2020)    ║
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
    self.service_title = 'Servicio de revisiones de mascotas' # Título con descripción del servicio
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

          tx_option = client_data['tx_option'] # Opción seleccionada por el cliente

          if tx_option == 1: # ======================== Registro de nueva revisión de mascota
            print(INSTRUCTIONS_STYLE+'\t- Funcionalidad requerida: Registro de nueva revisión de mascota'+Style.RESET_ALL)

            if client_data['tx_sub_option'] == 1: # ========== Validación de ID de mascota
              print(INSTRUCTIONS_STYLE+'\t- Subfuncionalidad requerida: Validación de ID de mascota'+Style.RESET_ALL)
              # Se verifica si el ID de mascota ingresado corresponde al de alguna mascota registrada.
              sql_query = '''
                SELECT Mascotas.*, Usuarios.rut AS rut_propietario, Usuarios.nombres AS nombres_propietario, Usuarios.apellidos AS apellidos_propietario
                  FROM Mascotas, Usuarios
                    WHERE Mascotas.rut_propietario = Usuarios.rut
                    AND Mascotas.id = %s
              '''

              resp_data = {'pet_exists': False, 'error_notification': 'No se ha encontrado una mascota registrada según el ID de mascota ingresado.'}

              cursor = self.db.query(sql_query, (client_data['pet_id'],))
              pet_reg = cursor.fetchone()

              if pet_reg is not None:
                # La mascota se encuentra registrada
                pet_reg['fecha_nacimiento'] = str(pet_reg['fecha_nacimiento']) # Se transforma de datetime a string
                resp_data = {'pet_exists': True, 'pet_data': pet_reg}
              
              else:
                # La mascota no se encuentra registrada, por lo tanto se notifica el error.
                resp_data = {'pet_exists': False, 'error_notification': 'No se ha encontrado una ficha de mascota registrada según el ID de mascota ingresado.'}
            
            if client_data['tx_sub_option'] == 2: # ========== Confirmación de registro de nueva revisión de mascota
              print(INSTRUCTIONS_STYLE+'\t- Subfuncionalidad requerida: Confirmación de registro de nueva revisión de mascota'+Style.RESET_ALL)
              
              # Se registra en la base de datos la nueva revisión
              review_data = client_data['review_data']
              sql_query = '''
                INSERT INTO Revisiones (id_mascota, rut_veterinario, fecha_revision, motivo_revision, diagnostico)
                  VALUES (%s, %s, %s, %s, %s)
              '''
              self.db.query(sql_query, (review_data['id_mascota'], review_data['rut_veterinario'], review_data['fecha_revision'], review_data['motivo_revision'], review_data['diagnostico']))

              resp_data = {'success': True, 'success_notification': 'La revisión ha sido registrada correctamente.'}

          elif tx_option == 2: # ======================== Ver detalle de revisiones registradas
            print(INSTRUCTIONS_STYLE+'\t- Funcionalidad requerida: Ver detalle de revisiones registradas'+Style.RESET_ALL)

            if client_data['tx_sub_option'] == 1: # ========== Validación de ID de mascota
              print(INSTRUCTIONS_STYLE+'\t- Subfuncionalidad requerida: Validación de ID de mascota'+Style.RESET_ALL)

              sql_query = '''
                SELECT Mascotas.id, Mascotas.nombre, Usuarios.rut AS rut_propietario, Usuarios.nombres AS nombres_propietario, Usuarios.apellidos AS apellidos_propietario
                  FROM Mascotas, Usuarios
                    WHERE Mascotas.rut_propietario = Usuarios.rut
                    AND Mascotas.id = %s
              '''
              cursor = self.db.query(sql_query, (client_data['pet_id'],))
              pet_reg = cursor.fetchone()

              if pet_reg is not None:
                # La ficha de mascota se encuentra registrada.
                resp_data = {'pet_exists': True}

                # Se obtiene la lista de revisiones registradas
                sql_query = '''
                  SELECT id, fecha_revision
                    FROM Revisiones
                      WHERE id_mascota = %s
                '''
                cursor = self.db.query(sql_query, (client_data['pet_id'],))
                review_list = cursor.fetchall()

                for review in review_list:
                  review['fecha_revision'] = str(review['fecha_revision'])

                resp_data['review_list'] = review_list
                
              else:
                # La ficha de mascota no se encuentra registrada. Se notifica al cliente.
                resp_data = {'pet_exists': False, 'error_notification': 'No se ha encontrado una ficha de mascota registrada según el ID de mascota ingresado.'}

            elif client_data['tx_sub_option'] == 2: # ========== Obtención de detalle de revisión
              print(INSTRUCTIONS_STYLE+'\t- Subfuncionalidad requerida: Obtención de detalle de revisión'+Style.RESET_ALL)

              # Se obtiene la ficha de mascota
              sql_query = '''
                SELECT * 
                  FROM Mascotas
                    WHERE id = %s
              '''
              cursor = self.db.query(sql_query, (client_data['pet_id'],))
              pet_reg = cursor.fetchone()

              if pet_reg is not None:
                pet_reg['fecha_nacimiento'] = str(pet_reg['fecha_nacimiento'])

              # Se obtiene la información de la revisión
              sql_query = '''
                SELECT *
                  FROM Revisiones
                    WHERE id = %s
                    AND id_mascota = %s
              '''
              cursor = self.db.query(sql_query, (client_data['review_id'], client_data['pet_id']))
              review_reg = cursor.fetchone()
              
              if review_reg is not None:
                review_reg['fecha_revision'] = str(review_reg['fecha_revision'])

              resp_data = {'success': True, 'pet_data': pet_reg, 'review_data': review_reg}
          
          elif tx_option == 3: # ======================== Modificación de revisión
            print(INSTRUCTIONS_STYLE+'\t- Funcionalidad requerida: Modificación de revisión'+Style.RESET_ALL)

            if client_data['tx_sub_option'] == 1: # ========== Obtención de lista de revisiones realizadas por el usuario
              print(INSTRUCTIONS_STYLE+'\t- Subfuncionalidad requerida: Obtención de lista de revisiones realizadas por el usuario.'+Style.RESET_ALL)

              # Se obtiene la lista de revisiones asociadas al RUT ingresado
              sql_query = '''
                SELECT Revisiones.id, Revisiones.fecha_revision AS 'Fecha de revisión', Mascotas.nombre AS 'Nombre de mascota', CONCAT(Usuarios.nombres, ' ', Usuarios.apellidos) AS 'Nombre de propietario'
                  FROM Revisiones, Mascotas, Usuarios
                    WHERE Revisiones.id_mascota = Mascotas.id
                    AND Mascotas.rut_propietario = Usuarios.rut
                    AND Revisiones.rut_veterinario = %s
              '''
              cursor = self.db.query(sql_query, (client_data['rut_usuario'],))

              review_list = cursor.fetchall()
              
              for review in review_list:
                review['Fecha de revisión'] = str(review['Fecha de revisión'])

              resp_data = {'success': True, 'review_list': review_list}
            
            elif client_data['tx_sub_option'] == 2: # ========== Obtención de detalle de revisión seleccionada
              print(INSTRUCTIONS_STYLE+'\t- Subfuncionalidad requerida: Obtención de detalle de revisión seleccionada.'+Style.RESET_ALL)

              # Se obtiene el detalle de la revisión seleccionada.
              sql_query = '''
                SELECT * 
                  FROM Revisiones
                    WHERE id = %s
              '''
              cursor = self.db.query(sql_query, (client_data['review_id'],))

              review_reg = cursor.fetchone()
              review_reg['fecha_revision'] = str(review_reg['fecha_revision'])

              if review_reg is not None:
                # Se obtuvo correctamente el registro de la revisión seleccionada.
                resp_data = {'success': True, 'review_data': review_reg}
              
              else:
                # La revisión seleccionada no se encuentra registrada.
                resp_data = {'success': False, 'error_notification': 'La revisión seleccionada ya no se encuentra registrada.'}
              
            
            elif client_data['tx_sub_option'] == 3: # ========== Confirmación de modificación de revisión
              print(INSTRUCTIONS_STYLE+'\t- Subfuncionalidad requerida: Confirmación de modificación de revisión.'+Style.RESET_ALL)

              # Se realiza la modificación de los campos según el formulario recibido.
              sql_query = '''
                UPDATE Revisiones
                  SET motivo_revision = %s, diagnostico = %s
                    WHERE id = %s
              '''
              self.db.query(sql_query, (client_data['review_data']['motivo_revision'], client_data['review_data']['diagnostico'], client_data['review_data']['id']))

              resp_data = {'success': True, 'success_notification': 'La revisión ha sido modificada correctamente.'}
          
          elif tx_option == 4: # ======================== Eliminación de revisión
            print(INSTRUCTIONS_STYLE+'\t- Funcionalidad requerida: Eliminación de revisión'+Style.RESET_ALL)

            # Se verifica si existe el registro de la revisión según el ID de revisión ingresado.
            sql_query = '''
              SELECT rut_veterinario
                FROM Revisiones
                  WHERE id = %s
            '''
            cursor = self.db.query(sql_query, (client_data['review_id'],))

            review_reg = cursor.fetchone()

            if review_reg is not None:
              # El registro de la revisión existe.

              # Se verifica si el registro lo realizó el usuario que quiere eliminarlo.
              if client_data['rut_usuario'].lower() == review_reg['rut_veterinario'].lower():
                # El usuario que solicita la eliminación realizó el registro, por lo tanto se elimina.
                sql_query = '''
                  DELETE FROM Revisiones
                    WHERE id = %s
                '''
                self.db.query(sql_query, (client_data['review_id'],))
              
                resp_data = {'success': True, 'success_notification': 'La revisión seleccionada ha sido eliminada correctamente.'}
              
              else:
                # El usuario que solicita la eliminación NO realizó el registro, por lo tanto se notifica el error.
                resp_data = {'success': False, 'error_notification': 'Este registro de revisión no puede ser eliminado con tu cuenta.'}

            else:
              # El registro de la revisión no existe, por lo tanto se notifica el error.
              resp_data = {'success': False, 'error_notification': 'La revisión seleccionada ya no se encuentra registrada.'}

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