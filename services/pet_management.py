# pylint: disable=unused-variable
# pylint: enable=too-many-lines

# ╔═════════════════════════════════════════════════════════════════════════════════════════════╗
# ║ Servicio de gestión de mascotas para proyecto de Arquitectura de Sistemas (02 - 2020)       ║
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
    self.service_title = 'Servicio de gestión de mascotas' # Título con descripción del servicio
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

          if tx_option == 0: # ============================================== Funcionalidad de agregar nueva mascota
            print(INSTRUCTIONS_STYLE+'\t- Funcionalidad requerida: Registro de nueva mascota'+Style.RESET_ALL)

            if client_data['tx_sub_option'] == 1: # Validación de RUT de propietario
              print(INSTRUCTIONS_STYLE+'\t- Subfuncionalidad requerida: Validación de RUT de propietario'+Style.RESET_ALL)
              # Se verifica que el RUT esté asociado a un usuario registrado
              sql_query = '''
                SELECT rut, nombres, apellidos
                  FROM Usuarios
                    WHERE rut = %s
              '''
              cursor = self.db.query(sql_query, (client_data['rut_propietario'],))

              user_data = cursor.fetchone()

              if user_data is not None:
                # Existe un usuario con el RUT ingresado
                resp_data = {'user_exists': True, 'user_data': user_data}
              
              else:
                # No se ha encontrado un usuario con el RUT ingresado
                resp_data = {'user_exists': False, 'error_notification': 'No se ha encontrado un usuario registrado según el RUT especificado.'}
            
            elif client_data['tx_sub_option'] == 2: # Confirmación de registro de mascota
              print(INSTRUCTIONS_STYLE+'\t- Subfuncionalidad requerida: Confirmación de registro de mascota'+Style.RESET_ALL)

              # Se convierte la fecha recibida para generarla mediante datetime
              client_data['pet_data']['fecha_nacimiento'] = client_data['pet_data']['fecha_nacimiento'].split('/')
              client_data['pet_data']['fecha_nacimiento'] = datetime(
                year = int(client_data['pet_data']['fecha_nacimiento'][2]),
                month = int(client_data['pet_data']['fecha_nacimiento'][1]),
                day = int(client_data['pet_data']['fecha_nacimiento'][0])
              ).date()

              # Se registran la mascota según los datos ingresados
              sql_query = '''
                INSERT INTO Mascotas (rut_propietario, nombre, especie, sexo, fecha_nacimiento, raza, tamano, peso, color, patron_color, esterilizado, tiene_microchip, numero_microchip, residencia)
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
              '''
              self.db.query(sql_query, tuple(client_data['pet_data'].values()))

              resp_data = {'registered': True, 'success_notification': 'La mascota ha sido registrada correctamente según los datos ingresados.'}
          
          elif tx_option == 1: # ============================================== Ver ficha de mascota
            print(INSTRUCTIONS_STYLE+'\t- Funcionalidad requerida: Ver ficha de mascota'+Style.RESET_ALL) 

            # Se obtiene la posible ficha de registro en la base de datos según el ID de mascota especificado
            sql_query = '''
              SELECT Usuarios.rut AS rut_propietario, Usuarios.nombres AS nombres_propietario, Usuarios.apellidos AS apellidos_propietario, Mascotas.*
                FROM Mascotas, Usuarios
                  WHERE Mascotas.id = %s
                  AND Usuarios.rut = Mascotas.rut_propietario
            '''

            cursor = self.db.query(sql_query, (client_data['pet_id'],))
            pet_reg = cursor.fetchone()

            if pet_reg is not None:
              # La ficha de la mascota se encuentra registrada
              pet_reg['fecha_nacimiento'] = str(pet_reg['fecha_nacimiento']) # Se transforma el objeto de fecha a un string
              
              resp_data = {'pet_exists': True, 'pet_data': pet_reg}
            
            else:
              # La ficha de la mascota no se encuentra registrada
              resp_data = {'pet_exists': False, 'error_notification': 'No se ha encontrado una ficha de mascota asociada al ID de mascota ingresado.'}

          elif tx_option == 2: # ============================================== Modificar ficha de mascota
            print(INSTRUCTIONS_STYLE+'\t- Funcionalidad requerida: Modificar ficha de mascota'+Style.RESET_ALL)

            if client_data['tx_sub_option'] == 1: # ============================================== Validación de RUT de propietario
              print(INSTRUCTIONS_STYLE+'\t- Subfuncionalidad requerida: Validación de ID de mascota'+Style.RESET_ALL)

              # Se obtiene el posible registro de la ficha de mascota según el ID ingresado
              sql_query = '''
                SELECT id, nombre, especie, sexo, fecha_nacimiento, raza, tamano, peso, color, patron_color, esterilizado, tiene_microchip, numero_microchip, residencia
                  FROM Mascotas
                    WHERE id = %s
              '''
              cursor = self.db.query(sql_query, (client_data['pet_id'],))

              pet_reg = cursor.fetchone()

              if pet_reg is not None:
                # La ficha de mascota se encuentra registrada
                pet_reg['fecha_nacimiento'] = str(pet_reg['fecha_nacimiento']) # Se transforma el objeto de fecha a un string

                resp_data = {'pet_exists': True, 'pet_data': pet_reg}

              else:
                # La ficha de mascota no se necuentra registrada
                resp_data = {'pet_exists': False, 'error_notification': 'No se ha encontrado una ficha de mascota asociada al ID de mascota ingresado.'}
            
            elif client_data['tx_sub_option'] == 2: # ============================================== Confirmación de modificación de ficha de mascota
              print(INSTRUCTIONS_STYLE+'\t- Subfuncionalidad requerida: Confirmación de modificación de ficha de mascota'+Style.RESET_ALL) 

              query_replace_str = ''

              for attr in client_data['pet_data'].keys():
                if attr == 'id':
                  continue

                replace = str(attr)+' = %s, '
                query_replace_str += replace
              
              # Se reemplaza la última ',' de la cadena de atributos a reemplazar
              query_replace_str = replace_last(query_replace_str, ',', '')

              pet_id = client_data['pet_data']['id']
              del client_data['pet_data']['id']

              # Se modifica el registro del usuario
              sql_query = 'UPDATE Mascotas SET '+query_replace_str+' WHERE id = %s'
              
              values = tuple(client_data['pet_data'].values())
              values += (pet_id,)

              self.db.query(sql_query, values)

              resp_data = {'success': True, 'success_notification': 'La ficha de mascota ha sido modificada correctamente.'}
          
          elif tx_option == 3: # ============================================== Eliminar ficha de mascota
            print(INSTRUCTIONS_STYLE+'\t- Funcionalidad requerida: Eliminación de ficha de mascota'+Style.RESET_ALL)

            pet_id = client_data['pet_id']

            # Se verifica si existe el registro de la ficha a eliminar
            sql_query = '''
              SELECT COUNT(*) AS cantidad_registros
                FROM Mascotas
                  WHERE id = %s
            '''
            cursor = self.db.query(sql_query, (pet_id,))
            cantidad_registros = cursor.fetchone()['cantidad_registros']

            if cantidad_registros == 0:
              # No existe una ficha de mascota asociada al ID de mascota ingresado. Se notifica el error.
              resp_data = {'success': False, 'error_notification': 'No se ha encontrado una ficha de mascota asociada al ID de mascota ingresado.'}
            
            else:
              # La mascota se encuentra registrada. Por lo tanto se elimina y se notifica al usuario.
              sql_query = '''
                DELETE FROM Mascotas
                  WHERE id = %s
              '''
              self.db.query(sql_query, (pet_id,))

              # Se eliminan las posibles revisiones asociadas
              sql_query = '''
                DELETE FROM Revisiones
                  WHERE id_mascota = %s
              '''
              self.db.query(sql_query, (pet_id,))

              # Se obtienen los IDs de las revisiones para eliminar los posibles insumos
              #sql_query = '''
              #  SELECT id
              #    FROM Revisiones
              #      WHERE id_mascota = %s
              #'''
              #cursor = self.db.query(sql_query, (pet_id,))
              #reviews_list = cursor.fetchall()

              #for review in reviews_list:
              #  sql_query = '''
              #    SELECT id_insumo
              #      FROM InsumosRevisiones
              #        WHERE id_revision = %s
              #  '''
              #  cursor = self.db.query(sql_query, (review['id'],))
              #  supplies_list = cursor.fetchall()
              #  supplies_list = [supplie['id_insumo'] for supplie in supplies_list]

              #  sql_query = '''
              #    DELETE FROM 
              #      Insumos
              #        WHERE id in {0}
              #  '''
              #  supplies_list_str = str(supplies_list).replace("[","(").replace("]",")")
              #  sql_query = sql_query.format(supplies_list_str)
              #  self.db.query(sql_query, None)


              resp_data = {'success': True, 'success_notification': 'La ficha de mascota ha sido eliminada correctamente.'}

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