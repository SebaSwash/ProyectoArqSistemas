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
from consolemenu import *
from consolemenu.items import *

from getpass import getpass
import socket, argparse, os, pickle
from terminaltables import AsciiTable
from colorama import Back, Fore, Style, init
from prettytable import PrettyTable

# Inicialización para librería de colores
init()

# Función para limpiar pantalla
def clear_screen():
  os.system('cls' if os.name == 'nt' else 'clear')

# Constantes con nombres de servicios a utilizar (06 corresponde al número de grupo de proyecto)
USER_AUTH_SERVICE_NAME = 'uas06'
USER_MANAGEMENTE_SERVICE_NAME = 'ums06'

# Constantes para combinaciones de colores y estilos (Back -> color de fondo, Fore -> color de texto)
INSTRUCTIONS_STYLE = Back.WHITE + Fore.BLACK
ERROR_STYLE = Back.RED + Fore.WHITE
WARNING_STYLE = Back.YELLOW + Fore.WHITE
INFO_STYLE = Back.BLUE + Fore.WHITE
SUCCESS_STYLE = Back.GREEN + Fore.WHITE

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
      print(ERROR_STYLE+'[Error] Se ha producido el siguiente error al establecer conexión con el bus de servicios:')
      print(str(error)+Style.RESET_ALL)
  
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
    #table_data = [
    #  ['Tus datos personales'],
    #  ['Nombre: '+str(user_data['nombres'])+' '+str(user_data['apellidos'])],
    #  ['RUT: '+str(user_data['rut'])],
    #  ['Email: '+str(user_data['email'])],
    #  ['Dirección: '+str(user_data['direccion'])],
    #  ['Tipo de credencial: '+str(user_data['tipo_usuario'])]
    #]

    # Se instancia el objeto de la tabla con los datos generados y se imprime en la terminal
    #table = AsciiTable(table_data)
    #print(table.table)

    clear_screen()
    menu = ConsoleMenu('Hola nuevamente, '+str(user_data['nombres'])+' '+str(user_data['apellidos']), 'Selecciona una de las opciones a continuación.')
    menu.append_item(SelectionItem('Sección de usuarios',0))
    menu.append_item(SelectionItem('Sección de mascotas',1))
    menu.append_item(SelectionItem('Sección de revisiones de mascotas',2))
    menu.append_item(SelectionItem('Cerrar sesión',3))
    menu.show(False) # False evita que se muestra la opción de 'exit' que viene por defecto

    user_option = menu.selected_option

    if user_option == 0: # Sección de usuarios
      # Se envía la solicitud al servicio de usuarios para obtener el menú interno
      data = {'tx_option': 0} # La opción 0 solicita al servicio el retorno del menú principal
      tx = self.generate_tx(USER_MANAGEMENTE_SERVICE_NAME, str(data))

      # Se envía la transacción para obtener el menú interno de la gestión de usuarios
      self.sock.send(tx.encode(encoding='UTF-8'))

      try:
        recv_tx = self.sock.recv(4096).decode('UTF-8')
        tx_length, tx_service, tx_status, tx_data = self.split_recv_tx(recv_tx)

        # Se verifica el estado de la transacción ('OK' o 'NK') según el bus de servicios.
        if tx_status.lower() == 'nk':
          # Se ha producido un error en la transferencia de la transacción
          print(Style.RESET_ALL)
          print(ERROR_STYLE+'[Error] Se ha producido un error en la transferencia de la transacción (NK).'+Style.RESET_ALL)
        
        tx_data = eval(tx_data)
        # Se genera el menú a partir de las opciones recibidas desde el servicio
        menu_options = tx_data['menu_options']

        # Se instancia el objeto del menú
        menu = ConsoleMenu(tx_data['menu_title'], tx_data['menu_subtitle'])
        index = 0
        for option in menu_options:
          menu.append_item(SelectionItem(option, index))
          index += 1
        
        menu.show(False)
        user_option = menu.selected_option

        if user_option == 0:
          # Se selecciona la opción de ver lista de usuarios registrados

          # Se genera la transacción para obtener desde el servicio la lista de usuarios
          data = {'tx_option': 1}

          tx = self.generate_tx(USER_MANAGEMENTE_SERVICE_NAME, str(data))

          # Se envía la solicitud al servicio y se verifica si se envía devuelta la lista o una notificación de error
          self.sock.send(tx.encode(encoding='UTF-8'))

          recv_tx = self.sock.recv(4096)
          # Se procesa la respuesta recibida desde el servicio a través del bus
          tx_length, tx_service, tx_status, tx_data = self.split_recv_tx(recv_tx)

          # Se verifica el estado de la transacción ('OK' o 'NK') según el bus de servicios.
          if tx_status.lower() == 'nk':
            # Se ha producido un error en la transferencia de la transacción
            print(Style.RESET_ALL)
            print(ERROR_STYLE+'[Error] Se ha producido un error en la transferencia de la transacción (NK).'+Style.RESET_ALL)
          
          # Se transforma el diccionario recibido y se procesa
          try:
            data = eval(tx_data.decode('UTF-8'))
            users_list = data['users_list']

            if len(users_list) != 0:
              # Se genera la tabla con la lista de usuarios obtenidas
              users_table = PrettyTable()

              # Se agregan las columnas, según los atributos recibidos
              users_table.field_names = list(users_list[0].keys())
              
              # Se agregan las filas en la tabla según cada usuario registrado
              for user in users_list:
                # Se transforma el diccionario en una lista con los valores de la información del usuario
                users_table.add_row(list(user.values()))
              
              # Se imprime en la terminal la tabla generada
              print(INSTRUCTIONS_STYLE+'================================= Lista de usuarios registrados'+Style.RESET_ALL)
              print(users_table)
          
          except Exception as error:
            print(ERROR_STYLE+'[Error] Se ha producido el siguiente error al procesar la información recibida:')
            print(str(error)+Style.RESET_ALL)

        # Se muestra el menú generado
        input('')
        clear_screen()
        menu.show(False)
      
      except Exception as error:
        print(ERROR_STYLE+'[Error] Se ha producido el siguiente error al desplegar el menú interno:')
        print(str(error)+Style.RESET_ALL)

      pass

    elif user_option == 1: # Sección de mascotas
      return

    elif user_option == 2: # Sección de revisiones de mascotas
      return

    elif user_option == 3: # Cerrar sesión
      return
  
  # Método para menú y opción de autentificación
  def user_menu_options(self):
    clear_screen()
    menu = ConsoleMenu('Bienvenid@ a la clínica veterinaria!', 'Selecciona una de las opciones a continuación.')
    menu.append_item(SelectionItem('Ingresar al sistema',0))
    menu.append_item(SelectionItem('Salir',1))
    menu.show(False) # False evita que se muestra la opción de 'exit' que viene por defecto

    user_option = menu.selected_option

    if user_option == 0:
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
          print(Style.RESET_ALL)
          print(ERROR_STYLE+'[Error] Se ha producido un error en la transferencia de la transacción (NK).'+Style.RESET_ALL)
        
        else: # La transacción fue recibida correctamente
          # Se verifica si se pudo autenticar al usuario
          user_data = eval(tx_data) # Se transforma el objeto como string a diccionario nuevamente
          if not user_data['auth_error']:
            # El usuario fue autenticado correctamente
            # Se muestra el siguiente menú interno con los otros servicios
            self.internal_menu_options(user_data)
          
          else:
            # Hubo un error al autentificar al usuario. Se muestra el mensaje de error enviado por el servicio.
            print(Style.RESET_ALL)
            print(ERROR_STYLE+'[Error] El servicio de autenticación ha respondido con el siguiente error:')
            print(user_data['error_notification']+Style.RESET_ALL)
      
      except Exception as error:
        print(Style.RESET_ALL)
        print(ERROR_STYLE+'[Error] Se ha producido el siguiente error al procesar la transacción:')
        print(str(error)+Style.RESET_ALL)

    elif user_option == 1:
      print(Style.RESET_ALL)
      print(INFO_STYLE+'Hasta luego!'+Style.RESET_ALL)
      self.sock.close()
      exit()
    
    input(INSTRUCTIONS_STYLE+'\nPresiona ENTER para continuar'+Style.RESET_ALL)

  def run(self):
    while True:
      try:
        # Ciclo de ejecución del proceso cliente
        self.user_menu_options()
      
      except KeyboardInterrupt:
        print(Style.RESET_ALL)
        clear_screen()
        exit()

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

  clear_screen()

  # Se instancia el objeto de la clase cliente
  client = Client(host, port)
