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
from prettytable import PrettyTable
from terminaltables import AsciiTable
import socket, argparse, os, pickle, bcrypt
from colorama import Back, Fore, Style, init

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
WARNING_STYLE = Back.YELLOW + Fore.BLACK
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
  
  def user_management_gui(self):

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
    
    except Exception as error:
      print(ERROR_STYLE+'[Error] Se ha producido el siguiente error al desplegar el menú interno:')
      print(str(error)+Style.RESET_ALL)
    
    # Menú y opciones de la interfaz de la gestión de usuarios
    while True:
      menu.show(False)
      user_option = menu.selected_option

      # ====================== OPCIÓN PARA VER LISTA DE USUARIOS (OP 1) ==============================
      if user_option == 0: 
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
            print('\n'+INSTRUCTIONS_STYLE+'Lista de usuarios registrados'+Style.RESET_ALL)
            print('')
            print(users_table)
            
        except Exception as error:
          print(ERROR_STYLE+'[Error] Se ha producido el siguiente error al procesar la información recibida:')
          print(str(error)+Style.RESET_ALL)
      
      # ====================== OPCIÓN PARA AGREGAR NUEVO USUARIO (OP 2) ==============================
      elif user_option == 1: 
        try:

          register_confirm = False # Flag para confirmar el registro de usuario
          # Se genera un objeto para almacenar todos los valores del formulario
          user_data = {}

          while True:
            print('\n'+INSTRUCTIONS_STYLE+'[Agregar usuario] Ingresa los datos del usuario a continuación.'+Style.RESET_ALL)
            print('')
  
            user_data['rut'] = input('- RUT: ')
            user_data['nombres'] = input('- Nombres: ')
            user_data['apellidos'] = input('- Apellidos: ')
            user_data['email'] = input('- Email: ')
            user_data['direccion'] = input('- Dirección: ')

            user_data['tipo_usuario'] = input('- Tipo de usuario (1 - Funcionario | 2 - Cliente): ')
            while user_data['tipo_usuario'] not in ['1', '2']:
              user_data['tipo_usuario'] = input('- Tipo de usuario (1 - Funcionario | 2 - Cliente): ')
            
            # Se obtiene la contraseña y se realiza el proceso de hasheo con algoritmo Bcrypt
            plain_pwd = getpass('- Contraseña (mínimo 8 caracteres): ')
            while len(plain_pwd) < 8:
              plain_pwd = getpass('- Contraseña (mínimo 8 caracteres): ')

            user_data['password'] = bcrypt.hashpw(plain_pwd.encode(encoding='UTF-8'), bcrypt.gensalt())
            del plain_pwd # Se borra la variable con la contraseña en texto plano

            # Se muestra el resumen de los datos ingresados y se pregunta para confirmar el registro
            print('\n'+INSTRUCTIONS_STYLE+'Los datos a ingresar son los siguientes:'+Style.RESET_ALL)
            print('')
            for attr in user_data.keys():
              if attr == 'password':
                continue

              print('- '+attr+': '+user_data[attr])
            
            print('')
            print(INSTRUCTIONS_STYLE+'\nSelecciona una de las opciones:'+Style.RESET_ALL)
            print('')

            print('[1] Registrar')
            print('[2] Modificar formulario')
            print('[3] Volver al menú')

            print('')
            op = input('> ')

            while op not in ['1', '2', '3']:
              op = input('> ')
            
            op = int(op)

            if op == 1 or op == 3:
              if op == 1:
                register_confirm = True
              break

          if not register_confirm:
            # Se devuelve al menú de gestión de usuarios
            continue

          # Se registra al usuario según los datos ingresados

          # Se genera la transacción para enviarla al servicio de gestión de usuarios por el bus de servicios
          client_data = {}
          client_data['user_data'] = user_data
          client_data['tx_option'] = 2
          tx = self.generate_tx(USER_MANAGEMENTE_SERVICE_NAME, str(client_data))
          
          # Una vez generada la transacción, se envía al servicio a través del bus de servicios
          self.sock.send(tx.encode(encoding='UTF-8'))

          # Se recibe la respuesta desde el servicio
          recv_tx = self.sock.recv(4096)
          # Se procesa la respuesta recibida desde el servicio a través del bus
          tx_length, tx_service, tx_status, tx_data = self.split_recv_tx(recv_tx)

          # Se verifica el estado de la transacción ('OK' o 'NK') según el bus de servicios.
          if tx_status.lower() == 'nk':
            # Se ha producido un error en la transferencia de la transacción
            print(Style.RESET_ALL)
            print(ERROR_STYLE+'[Error] Se ha producido un error en la transferencia de la transacción (NK).'+Style.RESET_ALL)
          
          # Se procesa los datos recibidos
          recv_data = eval(tx_data.decode('UTF-8'))

          print('')

          # En caso de que haya ocurrido un error en el servicio, se muestra la notificación
          if 'internal_error' in recv_data.keys():
            if recv_data['internal_error']:
              print(ERROR_STYLE+'[Error] Se ha producido el siguiente error al realizar el proceso de registro de usuario:'+Style.RESET_ALL)
              print(ERROR_STYLE+recv_data['error_notification']+Style.RESET_ALL)
          
          if 'success' in recv_data.keys():
            # Se notifica en caso de que el servico haya rechazado los datos enviados al realizar su validación
            if not recv_data['success']:
              print(ERROR_STYLE+'[Error] Se ha producido el siguiente error al validar los datos en el servicio:'+Style.RESET_ALL)
              print(ERROR_STYLE+recv_data['error_notification']+Style.RESET_ALL)
          
            else:
              # En caso de que se haya registrado correctamente, se muestra la notificación de éxito
              print(SUCCESS_STYLE+recv_data['success_notification']+Style.RESET_ALL)
        
        except Exception as error:
          print(ERROR_STYLE+'[Error] Se ha producido el siguiente error al realizar el proceso de registro de usuario:'+Style.RESET_ALL)
          print(ERROR_STYLE+str(error)+Style.RESET_ALL)
      
      # ====================== OPCIÓN PARA VER DETALLE DE USUARIO (OP 3) ==============================
      elif user_option == 2:
        try:
          # Se obtiene el RUT del usuario a verificar
          print('\n'+INSTRUCTIONS_STYLE+'Revisar detalle de usuario .'+Style.RESET_ALL)
          print('')
          rut_usuario = input('Ingresa el RUT del usuario a consultar (sin guión ni puntos): ')
          while len(rut_usuario) < 8 or len(rut_usuario) >= 10:
            rut_usuario = input('Ingresa el RUT del usuario a consultar (sin guión ni puntos): ')
          
          # Se arma el objeto y se genera la transacción
          data = {'tx_option': 3, 'rut_usuario': rut_usuario}

          tx = self.generate_tx(USER_MANAGEMENTE_SERVICE_NAME, str(data))

          # Se envía la transacción al servicio a través del bus de servicios
          self.sock.send(tx.encode(encoding='UTF-8'))

          # Se recibe la respuesta desde el servicio
          recv_tx = self.sock.recv(4096)
          # Se procesa la respuesta recibida desde el servicio a través del bus
          tx_length, tx_service, tx_status, tx_data = self.split_recv_tx(recv_tx)

          # Se verifica el estado de la transacción ('OK' o 'NK') según el bus de servicios.
          if tx_status.lower() == 'nk':
            # Se ha producido un error en la transferencia de la transacción
            print(Style.RESET_ALL)
            print(ERROR_STYLE+'[Error] Se ha producido un error en la transferencia de la transacción (NK).'+Style.RESET_ALL)
          
          # Se procesa los datos recibidos
          recv_data = eval(tx_data.decode('UTF-8'))
          
          # Se verifica el flag de éxito
          if not recv_data['success']:
            # No se encontró el usuario con el rut ingresado.
            # Se muestra el mensaje de error en pantalla.
            print(ERROR_STYLE+'[Error]: '+recv_data['error_notification']+Style.RESET_ALL)
          
          else:
            # Se encontró información asociada al usuario
            user_data = recv_data['user_data']

            print('\n'+INSTRUCTIONS_STYLE+'Información asociada al usuario'+Style.RESET_ALL)
            print('')
            print('- RUT: '+user_data['rut'])
            print('- Nombre completo: '+user_data['nombres']+' '+user_data['apellidos'])
            print('- Email: '+user_data['email'])
            print('- Dirección: '+user_data['direccion'])
            print('- Tipo de usuario: '+user_data['tipo_usuario'])

            print('\n'+INSTRUCTIONS_STYLE+'Lista de mascotas asociadas al usuario'+Style.RESET_ALL)
            print('')

            if len(recv_data['pet_list']) == 0:
              # El usuario no tiene mascotas asociadas
              print(WARNING_STYLE+'* El usuario no tiene mascotas asociadas actualmente.')
            
            else:
              # Se genera la tabla con la información de cada mascota
              pet_table = PrettyTable()

              # Se agregan las columnas, según los atributos recibidos
              pet_table.field_names = list(recv_data['pet_list'][0].keys())
                
              # Se agregan las filas en la tabla según cada usuario registrado
              for pet in recv_data['pet_list']:
                # Se transforma el diccionario en una lista con los valores de la información del usuario
                pet_table.add_row(list(pet.values()))
                
              # Se imprime en la terminal la tabla generada
              print(pet_table)


        except Exception as error:
          print(ERROR_STYLE+'[Error] Se ha producido el siguiente error al realizar el proceso de revisión de detalle de usuario:'+Style.RESET_ALL)
          print(ERROR_STYLE+str(error)+Style.RESET_ALL)
      
      # ====================== OPCIÓN PARA MODIFICAR USUARIO (OP 4) ==============================
      elif user_option == 3:
        pass

      # ====================== OPCIÓN PARA ELIMINAR USUARIO (OP 5) ==============================
      elif user_option == 4:
        pass

      # ====================== OPCIÓN PARA VOLVER AL MENÚ DE OPCIONES (OP 6) ==============================
      elif user_option == 5:
        break

      input('\n'+INSTRUCTIONS_STYLE+'Presiona ENTER para continuar'+Style.RESET_ALL)
      clear_screen()

  # Método para menú y opciones internas de cada servicio
  def internal_menu_options(self, user_data):
    clear_screen()

    while True:
      menu = ConsoleMenu('Hola nuevamente, '+str(user_data['nombres'])+' '+str(user_data['apellidos']), 'Selecciona una de las opciones a continuación.')
      
      # Se diferencia el menú según el tipo de usuario

      if user_data['tipo_usuario'] == 1:
        # El usuario corresponde a un veterinario
        menu.append_item(SelectionItem('Sección de usuarios',0))
        menu.append_item(SelectionItem('Sección de mascotas',1))
        menu.append_item(SelectionItem('Sección de revisiones de mascotas',2))
        menu.append_item(SelectionItem('Cerrar sesión',3))
      
      elif user_data['tipo_usuario'] == 2:
        # El usuario corresponde a un cliente
        menu.append_item(SelectionItem('Cerrar sesión',3))
      
      menu.show(False) # False evita que se muestra la opción de 'exit' que viene por defecto

      user_option = menu.selected_option

      if user_option == 0 and user_data['tipo_usuario'] == 1: # ======================= Sección de usuarios

        # Se muestra el menú con las opciones internas del servicio de gestión de usuarios
        self.user_management_gui()

      elif user_option == 1 and user_data['tipo_usuario'] == 1: # Sección de mascotas
        return

      elif user_option == 2 and user_data['tipo_usuario'] == 1: # Sección de revisiones de mascotas
        return

      elif user_option == 3 and user_data['tipo_usuario'] == 1: # Cerrar sesión
        return
      
      elif user_option == 3 and user_data['tipo_usuario'] == 2: # Cerrar sesión
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
