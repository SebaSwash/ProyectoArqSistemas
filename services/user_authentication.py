# pylint: disable=unused-variable
# pylint: enable=too-many-lines

# ╔═════════════════════════════════════════════════════════════════════════════════════════════╗
# ║ Servicio de autenticación de usuarios para proyecto de Arquitectura de Sistemas (02 - 2020) ║
# ╠═════════════════════════════════════════════════════════════════════════════════════════════╣
# ║ Integrantes:                                                                                ║
# ║ * Lorenzo Alfaro Bravo                                                                      ║
# ║ * Flor Calla Lazo                                                                           ║
# ║ * Sebastián Toro Severino                                                                   ║
# ╚═════════════════════════════════════════════════════════════════════════════════════════════╝

# Módulos a utilizar
from db import db_wrapper
from db.db_credentials import *
import socket, argparse, bcrypt

class Service:
  def __init__(self, host, port, name):
    self.service_title = 'Servicio de autenticación de usuarios' # Título con descripción del servicio
    self.service_name = name # Nombre del servicio para reconocimiento del bus de servicios

    # Se realiza la conexión a la base de datos con las credenciales
    self.db = db_wrapper.Database(DB_HOST, DB_PORT, DB_USER, DB_PASSWD, DB_DATABASE)

    # Se genera el socket utilizando protocolo TCP
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
      self.sock.connect((host, int(port)))
      # En caso de conectar exitosamente, se guarda como atributo el host y el puerto
      self.host = host
      self.port = port

      self.bus_register() # Registro del servicio en el bus de servicios
      self.run() # Inicio de la ejecución del servicio

    except Exception as error:
      print('[Error] Se ha producido el siguiente error al establecer conexión con el bus de servicios:')
      print(str(error))
    
  # Registro del nombre de servicio en el bus previo a la ejecución
  def bus_register(self):
    try:
      tx_cmd = 'sinit'+self.service_name # Comando de registro de servicio ante el bus
      tx = self.generate_tx_length(len(tx_cmd)) + tx_cmd

      self.sock.send(tx.encode(encoding='UTF-8'))
      status = self.sock.recv(4096).decode('UTF-8')[10:12] # 'OK' (exitoso) o 'NK' (fallido)
    
    except Exception as error:
      print('[Error] Se ha producido el siguiente error al registrar el servicio:')
      print(str(error))
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
      tx = self.sock.recv(4096)

      if not tx:
        # Se cierra el servicio si no se reciben datos desde el socket
        self.sock.close()
        break

      try:
        tx = tx.decode('UTF-8')
        # Se procesa la transacción para obtener los componentes individuales
        tx_length, tx_service, tx_data = self.split_tx(tx)
        print('------------------------------------------------------------------------------')
        print('Transacción recibida desde cliente')
        print('\t- Largo de la transacción: ' +str(tx_length)+' ('+str(int(tx_length))+')')
        print('\t- Servicio invocado: '+str(tx_service))
        print('\t- Datos recibidos: '+str(tx_data))
        print('------------------------------------------------------------------------------')

        # Se revisa el número de operación recibido desde el cliente
        try:
          client_data = eval(tx_data)

          if client_data['tx_option'] == 1:
            # Autenticación de cuenta
            # Se revisa en la base de datos la existencia del usuario según el RUT y se obtiene el hash de la password si existe.
            sql_query = '''
              SELECT *
                FROM Usuarios
                  WHERE rut = %s
            '''
            cursor = self.db.query(sql_query, (client_data['user_rut'],)) # Se ejecuta la consulta en la base de datos
            user_reg = cursor.fetchone() # Se obtiene el registro único desde la base de datos

            if user_reg is not None:
              # El usuario se encuentra registrado en la base de datos
              # Se comprueba si la contraseña enviada hace match con el hash almacenado en el registro del usuario
              if bcrypt.checkpw(client_data['password'].encode(encoding='UTF-8'), user_reg['password'].encode(encoding='UTF-8')):
                # La contraseña ingresada es correcta. Se envían los datos personales (omitiendo el hash de la password)
                del user_reg['password']
                resp_data = user_reg
                resp_data['auth_error'] = False # Se agrega el flag de autenticación exitosa
              
              else:
                # La contraseña ingresada es incorrecta
                # # Se notifica con el error correspondiente
                resp_data = {'auth_error': True, 'error_notification': 'Se ha producido un error de credenciales. Revisa nuevamente los campos.'}

            else:
              # El usuario no se encuentra registrado en la base de datos
              # Se notifica con el error correspondiente
              resp_data = {'auth_error': True, 'error_notification': 'Se ha producido un error de credenciales. Revisa nuevamente los campos.'}
        
        except Exception as error:
          print(error)
          # Se genera el error y se envía al cliente
          resp_data = {'auth_error': True, 'error_notification': str(error)}
        
        # Se genera la transacción y se envía al cliente
        tx = self.generate_tx(str(resp_data)).encode(encoding='UTF-8')
        self.sock.send(tx)
      
      except Exception as error:
        # Se notifica el error al cliente y se imprime en el servicio
        print('[Error] Se ha producido el siguiente error al procesar la transacción:')
        print(str(error))
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
    print('[Error] El nombre del servicio debe ser de 5 caracteres. (Formato del bus de servicios)')
    exit()

  # Se instancia el objeto de la clase servicio
  service = Service(host, port, service_name)
