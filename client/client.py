# pylint: disable=unused-variable
# pylint: enable=too-many-lines

# ╔═══════════════════════════════════════════════════════════════════════╗
# ║ Proceso cliente para proyecto de Arquitectura de Sistemas (02 - 2020) ║
# ╠═══════════════════════════════════════════════════════════════════════╣
# ║ Integrantes:                                                          ║
# ║ * Lorenzo Alfaro Bravo                                                ║
# ║ * Flor Calla Lazo                                                     ║
# ║ * Sebastián Toro Severino                                             ║
# ╚═══════════════════════════════════════════════════════════════════════╝

# Módulos a utilizar
import socket, argparse, os
from getpass import getpass
from terminaltables import AsciiTable

# Función para limpiar pantalla
def clear_screen():
  os.system('cls' if os.name == 'nt' else 'clear')

# Constantes con nombres de servicios a utilizar
USER_AUTH_SERVICE_NAME = 'uauth'

class Client:
  def __init__(self, host, port):
    # Se genera el socket utilizando protocolo TCP
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Se intenta establecer la conexión mediante el host y puero seleccionado
    try:
      self.sock.connect((host, int(port)))
      # En caso de conectar exitosamente, se guarda como atributo el host y puerto
      self.host = host
      self.port = port

      self.run() # Inicio de la ejecución del proceso cliente
    
    except Exception as error:
      print('[Error] Se ha producido el siguiente error al establecer conexión con el bus de servicios:')
      print(str(error))
  
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
  def generate_tx(self, service, data):
    return self.generate_tx_length(len(service + data)) + service + data
  
  # Método para dividir la transacción recibida desde el servidor y separarla para verificar estado (OK/NK)
  def split_recv_tx(self, tx):
    tx_length = tx[:5] # Largo de la transacción
    tx_service = tx[5:10] # Servicio invocado
    tx_status = tx[10:12] # 'OK' (éxito) o 'NK' (fallido)
    tx_data = tx[12:] # Data recibida desde el servidor

    return (tx_length, tx_service, tx_status, tx_data)

  # Método para menú y opciones internas de cada servicio
  def internal_menu_options(self, user_data):
    # Se genera una tabla con los datos del usuario para mostrarlos en la terminal
    table_data = [
      ['Tus datos personales'],
      ['Nombre: '+str(user_data['user_name'])],
      ['RUT: '+str(user_data['user_rut'])],
      ['Email: '+str(user_data['email'])],
      ['Dirección: '+str(user_data['address'])],
      ['Tipo de credencial: '+str(user_data['user_type'])]
    ]

    # Se instancia el objeto de la tabla con los datos generados y se imprime en la terminal
    table = AsciiTable(table_data)
    print(table.table)

    # Se muestran a continuación las siguientes opciones de servicios
    input('ENTER para continuar')
  
  # Método para menú y opción de autentificación
  def user_menu_options(self):
    clear_screen()
    menu_table = '''
    ┌───────────────────────────────┐
    │ Bienvenido a My Pet's Friend! │
    ├───────────────────────────────┤
    │ [1] Iniciar sesión            │
    │ [2] Salir                     │
    └───────────────────────────────┘'''
    print(menu_table)
    user_option = input('Selecciona una de las opciones [1-2]: ')

    while user_option not in ['1','2']:
      user_option = input('Selecciona una de las opciones [1-2]: ')
    
    user_option = int(user_option) 

    if user_option == 1:
      # Se inicia el proceso de autenticación del usuario
      print('\n')
      user_rut = input('Ingresa tu RUT sin guión ni puntos: ')
      password = getpass('Ingresa tu contraseña: ') # getpass permite ocultar la password en la terminal.

      # Se genera el diccionario con los datos para realizar la autenticación en el servicio.
      user_data = {'user_rut': user_rut, 'password': password, 'tx_option': 1} # 'tx_option' permite al servidor reconocer la tx de autentificación obtenida.

      # Se genera la transacción (tx) en base al objeto creado
      tx = self.generate_tx(USER_AUTH_SERVICE_NAME, str(user_data)) # El objeto es tomado en formato string.

      # Se envía la transacción al servicio por medio del bus de servicios.
      self.sock.send(tx.encode(encoding='UTF-8'))

      # Se obtiene el resultado de la transacción desde el servicio
      # En caso de éxito, se reciben los datos personales del usuario y en caso de error, se obtiene una notificación de error.
      recv_tx = self.sock.recv(4096)

      try:
        recv_tx = recv_tx.decode('UTF-8')
        tx_length, tx_service, tx_status, tx_data = self.split_recv_tx(recv_tx)

        # Se verifica el estado de la transacción ('OK' o 'NK') según el bus de servicios.
        if tx_status.lower() == 'nk':
          # Se ha producido un error en la transferencia de la transacción
          print('[Error] Se ha producido un error en la transferencia de la transacción (NK).')
        
        else: # La transacción fue recibida correctamente
          # Se verifica si se pudo autenticar al usuario
          user_data = eval(tx_data) # Se transforma el objeto como string a diccionario nuevamente
          if not user_data['auth_error']:
            # El usuario fue autenticado correctamente
            # Se muestra el siguiente menú interno con los otros servicios
            print(user_data)
          
          else:
            # Hubo un error al autentificar al usuario. Se muestra el mensaje de error enviado por el servicio.
            print('[Error] El servicio de autenticación ha respondido con el siguiente error:')
            print(user_data['error_notification'])
      
      except Exception as error:
        print('[Error] Se ha producido el siguiente error al procesar la transacción:')
        print(str(error))

    elif user_option == 2:
      print('\nHasta luego!')
      self.sock.close()
      exit()
    
    input('\nPresiona ENTER para continuar')

  def run(self):
    # Ciclo de ejecución del proceso cliente
    while True:
      self.user_menu_options()

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
  args = parser.parse_args()

  # Se obtienen los valores de host y puerto especificados en el comando de la terminal
  host = args.host
  port = args.port

  # Se instancia el objeto de la clase cliente
  client = Client(host, port)
