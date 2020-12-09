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
from datetime import datetime
from prettytable import PrettyTable
from terminaltables import AsciiTable
from colorama import Back, Fore, Style, init
import socket, argparse, os, pickle, bcrypt, re

# Inicialización para librería de colores
init()

# Función para limpiar pantalla
def clear_screen():
  os.system('cls' if os.name == 'nt' else 'clear')

# Función para reemplazar últimos caracteres en strings
def replace_last(source_string, replace_what, replace_with):
  head, _sep, tail = source_string.rpartition(replace_what)
  return head + replace_with + tail

# Constantes con nombres de servicios a utilizar (06 corresponde al número de grupo de proyecto)
USER_AUTH_SERVICE_NAME = 'uas06'
USER_MANAGEMENTE_SERVICE_NAME = 'ums06'
PET_MANAGEMENT_SERVICE_NAME = 'pms06'
PET_REVIEWS_SERVICE_NAME = 'prs06'

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

      self.session = {} # Diccionario para almacenar datos del usuario en sesión

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
  
  # Método para obtener y procesar los datos recibidos desde el servicio por medio del bus
  def recv_data(self):
    # Se obtiene el resultado de la transacción desde el servicio
    recv_tx = self.sock.recv(10000)

    # Se procesa la respuesta recibida desde el servicio a través del bus
    tx_length, tx_service, tx_status, tx_data = self.split_recv_tx(recv_tx)

    # Se verifica el estado de la transacción ('OK' o 'NK') según el bus de servicios.
    if tx_status.lower() == 'nk':
      # Se ha producido un error en la transferencia de la transacción
      print(Style.RESET_ALL)
      print(ERROR_STYLE+'[Error] Se ha producido un error en la transferencia de la transacción (NK).'+Style.RESET_ALL)
      return False, None
    
    else:
      return True, tx_data
  
  def user_management_gui(self):
    # Se envía la solicitud al servicio de usuarios para obtener el menú interno
    data = {'tx_option': 0} # La opción 0 solicita al servicio el retorno del menú principal
    tx = self.generate_tx(USER_MANAGEMENTE_SERVICE_NAME, str(data))

    # Se envía la transacción para obtener el menú interno de la gestión de usuarios
    self.sock.send(tx.encode(encoding='UTF-8'))

    try:
      recv_tx = self.sock.recv(10000).decode('UTF-8')
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

        tx_ok, tx_data = self.recv_data()

        # Se omite el siguiente procesamiento, en caso de que hayan problemas con la recepción de la transacción
        if not tx_ok:
          continue
          
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

          tx_ok, tx_data = self.recv_data()

          # Se omite el siguiente procesamiento, en caso de que hayan problemas con la recepción de la transacción
          if not tx_ok:
            continue
          
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
          print('\n'+INSTRUCTIONS_STYLE+'Revisar detalle de usuario'+Style.RESET_ALL)
          print('')
          rut_usuario = input('Ingresa el RUT del usuario a consultar (sin guión ni puntos): ')
          while len(rut_usuario) < 8 or len(rut_usuario) >= 10:
            rut_usuario = input('Ingresa el RUT del usuario a consultar (sin guión ni puntos): ')
          
          # Se arma el objeto y se genera la transacción
          data = {'tx_option': 3, 'rut_usuario': rut_usuario}

          tx = self.generate_tx(USER_MANAGEMENTE_SERVICE_NAME, str(data))

          # Se envía la transacción al servicio a través del bus de servicios
          self.sock.send(tx.encode(encoding='UTF-8'))

          tx_ok, tx_data = self.recv_data()

          # Se omite el siguiente procesamiento, en caso de que hayan problemas con la recepción de la transacción
          if not tx_ok:
            continue
          
          # Se procesa los datos recibidos
          recv_data = eval(tx_data.decode('UTF-8'))
          
          # Se verifica el flag de éxito
          if not recv_data['success']:
            # No se encontró el usuario con el rut ingresado.
            # Se muestra el mensaje de error en pantalla.
            print('')
            print(ERROR_STYLE+'[Error]: '+recv_data['error_notification']+Style.RESET_ALL)
          
          else:
            # Se encontró información asociada al usuario
            clear_screen()
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
        try:
          print('\n'+INSTRUCTIONS_STYLE+'Modificación de usuario'+Style.RESET_ALL)
          print('')
          rut_usuario = input('Ingresa el RUT del usuario a modificar (sin guión ni puntos): ')

          while len(rut_usuario) < 8 or len(rut_usuario) >= 10:
            rut_usuario = input('Ingresa el RUT del usuario a modificar (sin guión ni puntos): ')
          
          # Se envía el rut del usuario al servicio para verificar y obtener los datos del mismo
          # * Sub option permite distinguir dentro de la misma funcionalidad de modificar, la opción de 
          # retorno de los datos del usuario según su RUT
          data = {'tx_option': 4, 'tx_sub_option': 1 , 'rut_usuario': rut_usuario}
          tx = self.generate_tx(USER_MANAGEMENTE_SERVICE_NAME, str(data))

          self.sock.send(tx.encode(encoding='UTF-8'))

          tx_ok, tx_data = self.recv_data()

          # Se omite el siguiente procesamiento, en caso de que hayan problemas con la recepción de la transacción
          if not tx_ok:
            continue

          data = eval(tx_data.decode('UTF-8'))

          print('')
          if data['user_exists']:
            clear_screen()
            user_data = data['user_data']
            # El usuario con el RUT ingresado se encuentra registrado
            print(INSTRUCTIONS_STYLE+'Información actual del usuario'+Style.RESET_ALL)
            print('')
            print('- RUT: '+user_data['rut'])
            print('- Nombre completo: '+user_data['nombres']+' '+user_data['apellidos'])
            print('- Email: '+user_data['email'])
            print('- Dirección: '+user_data['direccion'])
            print('- Tipo de usuario: '+user_data['tipo_usuario'])

            print('')
            print(INSTRUCTIONS_STYLE+'A continuación podrás modificar los campos del usuario.')
            print('En caso de querer mantener alguno de los datos, presiona ENTER sin rellenarlo.'+Style.RESET_ALL)
            print('')

            data = {'tx_option': 4, 'tx_sub_option': 2, 'user_data': {}}
            data['user_data']['rut_usuario'] = rut_usuario

            # Se despliegan los inputs a medida que se mantienen o modifican
            for attr in user_data.keys():

              if attr == 'rut':
                continue

              new_attr = input('- '+str(attr)+': ')

              if attr == 'tipo_usuario':
                while new_attr not in ['1', '2', '']:
                  new_attr = input('- '+str(attr)+': ')

              if len(new_attr) != 0:
                # Se registra el atributo cambiado en el objeto a enviar
                data['user_data'][attr] = new_attr
              
              else:
                # Se continúa en caso de que no se haya decidido modificar el campo
                continue
            
            # Se genera y envía la transacción al servicio para realizar la modificación
            tx = self.generate_tx(USER_MANAGEMENTE_SERVICE_NAME, str(data))
            
            self.sock.send(tx.encode(encoding='UTF-8'))

            # Se recibe la notificación de respuesta desde el servicio
            tx_ok, tx_data = self.recv_data()

            # Se omite el siguiente procesamiento, en caso de que hayan problemas con la recepción de la transacción
            if not tx_ok:
              continue

            # Se verifica el estado de la modificación (si se modificó o hubo un error) notificando al usuario
            tx_data = eval(tx_data.decode('UTF-8'))

            print('')
            if tx_data['mod_error']:
              print(ERROR_STYLE+'[Error] '+tx_data['error_notification']+Style.RESET_ALL)
            
            else:
              print(SUCCESS_STYLE+tx_data['success_notification']+Style.RESET_ALL)

          else:
            # No se ha encontrado el usuario con el RUT registrado
            print(ERROR_STYLE+'[Error] No se ha encontrado un usuario registrado según el RUT ingresado.'+Style.RESET_ALL)

        except Exception as error:
          print(ERROR_STYLE+'[Error] Se ha producido el siguiente error al realizar el proceso de revisión de modificación de usuario:'+Style.RESET_ALL)
          print(ERROR_STYLE+str(error)+Style.RESET_ALL)

      # ====================== OPCIÓN PARA ELIMINAR USUARIO (OP 5) ==============================
      elif user_option == 4:
        try:
          print('\n'+INSTRUCTIONS_STYLE+'Eliminación de usuario'+Style.RESET_ALL)
          print('')  

          rut_usuario = input('Ingresa el RUT del usuario a eliminar: ')

          data = {'tx_option': 5, 'rut_usuario': rut_usuario}

          # Se envía la transacción al servicio
          tx = self.generate_tx(USER_MANAGEMENTE_SERVICE_NAME, str(data))

          self.sock.send(tx.encode(encoding='UTF-8'))

          # Se recibe la notificación de éxito o error en la eliminación
          tx_ok, tx_data = self.recv_data()

          # Se omite el siguiente procesamiento, en caso de que hayan problemas con la recepción de la transacción
          if not tx_ok:
            continue

          tx_data = eval(tx_data.decode('UTF-8'))

          print('')
          if tx_data['delete_error']:
            print(ERROR_STYLE+'[Error] '+tx_data['error_notification']+Style.RESET_ALL)
            
          else:
            print(SUCCESS_STYLE+tx_data['success_notification']+Style.RESET_ALL)
        
        except Exception as error:
          print(ERROR_STYLE+'[Error] Se ha producido el siguiente error al realizar el proceso de eliminación de usuario:'+Style.RESET_ALL)
          print(ERROR_STYLE+str(error)+Style.RESET_ALL)

      # ====================== OPCIÓN PARA VOLVER AL MENÚ DE OPCIONES (OP 6) ==============================
      elif user_option == 5:
        break

      input('\n'+INSTRUCTIONS_STYLE+'Presiona ENTER para continuar'+Style.RESET_ALL)
      clear_screen()
  
  # Método para menú y opciones de la gestión de mascotas
  def pet_management_gui(self):
    # Se instancia el objeto del menú
    menu = ConsoleMenu('Menú de gestión de mascotas', 'Selecciona una de las opciones a continuación.')
    
    menu.append_item(SelectionItem('Registrar ficha de mascota', 0))
    menu.append_item(SelectionItem('Ver ficha de mascota', 1))
    menu.append_item(SelectionItem('Modificar ficha de mascota', 2))
    menu.append_item(SelectionItem('Eliminar ficha de mascota', 3))
    menu.append_item(SelectionItem('Volver', 4))

    while True:
      menu.show(False)
      user_option = menu.selected_option

      if user_option == 0: # ======= Registrar ficha de mascota

        print(INSTRUCTIONS_STYLE+'Registro de mascota'+Style.RESET_ALL)

        print('')
        rut_propietario = input('Ingresa el RUT del propietario (sin guión ni puntos): ')
        
        while len(rut_propietario) < 8 or len(rut_propietario) >= 10:
          rut_propietario = input('Ingresa el RUT del propietario (sin guión ni puntos): ')

        # Se genera y envía la transacción para validar el RUT del propietario
        # tx_option representa la opción de 'Agregar nueva mascota', mientras que
        # 'tx_sub_option' representa la validación del RUT del usuario
        data = {'tx_option': 0, 'tx_sub_option': 1, 'rut_propietario': rut_propietario}

        tx = self.generate_tx(PET_MANAGEMENT_SERVICE_NAME, str(data))

        self.sock.send(tx.encode(encoding='UTF-8'))

        tx_ok, tx_data = self.recv_data()

        if not tx_ok:
          continue

        data = eval(tx_data.decode('UTF-8'))

        if data['user_exists']:
          # Existe un usuario con el RUT ingresado. Se continúa con el registro de la mascota.
          print('')
          print(INSTRUCTIONS_STYLE+'Propietario seleccionado'+Style.RESET_ALL)
          print('')
          print('- RUT del propietario: ' +data['user_data']['rut'])
          print('- Nombre del propietario: '+data['user_data']['nombres']+' '+data['user_data']['apellidos'])
          print('')

          print(INSTRUCTIONS_STYLE+'Información de la mascota'+Style.RESET_ALL)
          print('')

          pet_data = {} # Diccionario para almacenar datos de la mascota
          pet_data['rut_propietario'] = rut_propietario

          pet_data['nombre'] = input('- Nombre: ')
          pet_data['especie'] = input('- Especie: ')
          pet_data['sexo'] = input('- Sexo [M (macho) / H (hembra)]: ').upper()

          while pet_data['sexo'].lower() not in ['m', 'h']:
            pet_data['sexo'] = input('- Sexo [M (macho) / H (hembra)]: ').upper()
          
          pet_data['fecha_nacimiento'] = input('- Fecha de nacimiento (dd/mm/aaaa): ')

          # Se comprueba la fecha de nacimiento con la expresión regular
          while not re.match('^[0-9]{2}\\/[0-9]{2}\\/[0-9]{4}$', pet_data['fecha_nacimiento']):
            pet_data['fecha_nacimiento'] = input('- Fecha de nacimiento (dd/mm/aaaa): ')

          pet_data['raza'] = input('- Raza: ')
          pet_data['tamaño'] = input('- Tamaño: ')
          pet_data['peso'] = input('- Peso (kg): ')
          pet_data['color'] = input('- Color: ')
          pet_data['patron_color'] = input('- Patrón de color: ')
          esterilizado = input('- ¿Esterilizado/a? [S/N]: ')

          while esterilizado.lower() not in ['s', 'n']:
            esterilizado = input('- ¿Esterilizado/a? [S/N]: ')
          
          if esterilizado.lower() == 's':
            pet_data['esterilizado'] = 1
          
          else:
            pet_data['esterilizado'] = 0
          
          tiene_microchip = input('- ¿Tiene microchip? [S/N]: ')

          while tiene_microchip.lower() not in ['s', 'n']:
            tiene_microchip= input('- ¿Tiene microchip? [S/N]: ')
          
          if tiene_microchip == 's':
            pet_data['tiene_microchip'] = 1
            pet_data['numero_microchip'] = input('- N° de microchip: ')

            while not pet_data['numero_microchip'].isnumeric():
              pet_data['numero_microchip'] = input('- N° de microchip: ')

          else:
            pet_data['tiene_microchip'] = 0
            pet_data['numero_microchip'] = None
          
          pet_data['residencia'] = input('- Residencia: ')

          print('')
          confirmation = input('Los datos serán enviados y se registrará la mascota. Por favor confirma esta operación [S/N]: ')
          while confirmation.lower() not in ['s', 'n']:
            confirmation = input('Los datos serán enviados y se registrará la mascota. Por favor confirma esta operación [S/N]: ')
          
          if confirmation.lower() == 's':
            # Se envían los datos para registrar la mascota
            
            # Se genera la transacción con los datos y se envía al servicio
            data = {'tx_option': 0 , 'tx_sub_option': 2, 'pet_data': pet_data}
            tx = self.generate_tx(PET_MANAGEMENT_SERVICE_NAME, str(data))

            self.sock.send(tx.encode(encoding='UTF-8'))

            tx_ok, tx_data = self.recv_data()

            print('')

            if tx_ok:
              data = eval(tx_data.decode('UTF-8'))
              # Se muestra la notificación recibida desde el servicio
              if data['registered']:
                print(SUCCESS_STYLE+data['success_notification']+Style.RESET_ALL)
                
        else:
          print('')
          # No se ha encontrado un usuario asociado al RUT ingresado.
          print(ERROR_STYLE+'[Error] '+data['error_notification']+Style.RESET_ALL)
      
      elif user_option == 1: # ======= Ver ficha de mascota
        print(INSTRUCTIONS_STYLE+'Ver ficha de mascota'+Style.RESET_ALL)
        print('')
        pet_id = input('Ingresa el ID de la mascota: ')

        # Se genera la transacción y se valida el ID de la mascota en el servicio
        data = {'tx_option': 1, 'pet_id': pet_id}

        tx = self.generate_tx(PET_MANAGEMENT_SERVICE_NAME, str(data))

        self.sock.send(tx.encode(encoding='UTF-8'))

        tx_ok, tx_data = self.recv_data()

        if tx_ok:
          data = eval(tx_data.decode('UTF-8'))
          
          if data['pet_exists']:

            clear_screen()

            # Se muestran los datos obtenidos de la ficha de mascota
            print('')
            print(INSTRUCTIONS_STYLE+'=================== Ficha de mascota ==================='+Style.RESET_ALL)
            print('')

            print(INSTRUCTIONS_STYLE+'=================== Datos del propietario'+Style.RESET_ALL)
            print('')
            print('- RUT: '+data['pet_data']['rut_propietario'])
            print('- Nombre: '+data['pet_data']['nombres_propietario']+' '+data['pet_data']['apellidos_propietario'])
            print('')

            print(INSTRUCTIONS_STYLE+'=================== Datos de la mascota'+Style.RESET_ALL)
            print('')
            print('- Nombre: '+data['pet_data']['nombre'])
            print('- Especie: '+data['pet_data']['especie'])
            print('- Sexo: '+data['pet_data']['sexo'])
            print('- Fecha de nacimiento: '+data['pet_data']['fecha_nacimiento'])
            print('- Raza: '+data['pet_data']['raza'])
            print('- Tamaño: '+data['pet_data']['tamano'])
            print('- Peso (kg): '+str(data['pet_data']['peso']))
            print('- Color: '+data['pet_data']['tamano'])
            print('- Patrón de color: '+data['pet_data']['patron_color'])
            print('- Esterilizado: '+ 'SI' if data['pet_data']['esterilizado'] else 'NO')
            print('- Residencia: '+data['pet_data']['residencia'])

            if data['pet_data']['tiene_microchip']:
              print('')
              print(INFO_STYLE+'* La mascota tiene microchip instalado.')
              print('- N° de microchip: '+ data['pet_data']['numero_microchip'] + Style.RESET_ALL)
            
            else:
              print('')
              print(WARNING_STYLE+'* La mascota NO tiene microchip instalado.'+Style.RESET_ALL)
          
          else:

            print('')
            print(ERROR_STYLE+'[Error] '+data['error_notification'])
      
      elif user_option == 2: # Modificar ficha de mascota
        print(INSTRUCTIONS_STYLE+'Modificar ficha de mascota'+Style.RESET_ALL)
        print('')
        pet_id = input('Ingresa el ID de la mascota: ')

        # Se genera la transacción y se valida el ID de la mascota en el servicio
        data = {'tx_option': 2, 'tx_sub_option': 1, 'pet_id': pet_id}

        tx = self.generate_tx(PET_MANAGEMENT_SERVICE_NAME, str(data))

        self.sock.send(tx.encode(encoding='UTF-8'))

        tx_ok, tx_data = self.recv_data()

        if tx_ok:
          data = eval(tx_data.decode('UTF-8'))

          if data['pet_exists']:
            # La ficha de mascota se encuentra registrada. Se continúa con la modificación del registro.
            clear_screen()
            print(INSTRUCTIONS_STYLE+'Ficha actual de la mascota'+Style.RESET_ALL)
            print('')
            print('- Nombre: '+data['pet_data']['nombre'])
            print('- Especie: '+data['pet_data']['especie'])
            print('- Sexo: '+data['pet_data']['sexo'])
            print('- Fecha de nacimiento: '+data['pet_data']['fecha_nacimiento'])
            print('- Raza: '+data['pet_data']['raza'])
            print('- Tamaño: '+data['pet_data']['tamano'])
            print('- Peso (kg): '+str(data['pet_data']['peso']))
            print('- Color: '+data['pet_data']['tamano'])
            print('- Patrón de color: '+data['pet_data']['patron_color'])
            print('- Esterilizado: '+ 'SI' if data['pet_data']['esterilizado'] else 'NO')
            print('- Residencia: '+data['pet_data']['residencia'])

            if data['pet_data']['tiene_microchip']:
              microchip = True
              print('')
              print(INFO_STYLE+'* La mascota tiene microchip instalado.')
              print('- N° de microchip: '+ data['pet_data']['numero_microchip'] + Style.RESET_ALL)
            
            else:
              microchip = False
              print('')
              print(WARNING_STYLE+'* La mascota NO tiene microchip instalado.'+Style.RESET_ALL)

            print('')
            print(INSTRUCTIONS_STYLE+'A continuación podrás modificar los campos del usuario.')
            print('En caso de querer mantener alguno de los datos, presiona ENTER sin rellenarlo.'+Style.RESET_ALL)
            print('')

            # Se despliegan los inputs a medida que se mantienen o modifican
            for attr in data['pet_data'].keys():

              if attr == 'id':
                continue

              if attr == 'numero_microchip' and not microchip:
                continue

              new_attr = input('- '+str(attr)+': ')

              if attr == 'sexo':
                while new_attr.lower() not in ['','m', 'h']:
                  new_attr = input('- '+str(attr)+' [M/H]: ')
                
                if new_attr.lower() in ['m', 'h']:
                  new_attr = new_attr.upper()
              
              elif attr == 'fecha_nacimiento':
                # Se comprueba la fecha de nacimiento con la expresión regular
                if len(new_attr) != 0:
                  while not re.match('^[0-9]{2}\\/[0-9]{2}\\/[0-9]{4}$', new_attr):
                    new_attr = input('- '+str(attr)+' (dd/mm/aaaa): ')
              
              elif attr == 'peso':
                if len(new_attr) != 0:
                  while new_attr.isnumeric() is not True:
                    new_attr = input('- '+str(attr)+': ')
              
              elif attr == 'esterilizado':
                if len(new_attr) != 0:
                  while new_attr.lower() not in ['s', 'n']:
                    new_attr = input('- '+str(attr)+' [S/N]: ')
              
              elif attr == 'tiene_microchip':
                if len(new_attr) != 0:
                  while new_attr not in ['s', 'n']:
                    new_attr = input('- '+str(attr)+' [S/N]: ')

              if len(new_attr) != 0:

                if attr == 'esterilizado':
                  if new_attr.lower() == 's':
                    new_attr = 1
                  else:
                    new_attr = 0
                
                elif attr == 'tiene_microchip':
                  if new_attr.lower() == 's':
                    new_attr = 1
                    microchip = True
                
                  else:
                    new_attr = 0
                    microchip = False
                    data['pet_data']['numero_microchip'] = None

                # Se registra el atributo cambiado en el objeto a enviar
                data['pet_data'][attr] = new_attr
              
              else:
                # Se continúa en caso de que no se haya decidido modificar el campo
                continue
            
            # Se genera la nueva transacción con los datos modificados y se envía al servicio
            new_data = {'tx_option': 2, 'tx_sub_option': 2, 'pet_data': data['pet_data']}

            tx = self.generate_tx(PET_MANAGEMENT_SERVICE_NAME, str(new_data))

            self.sock.send(tx.encode(encoding='UTF-8'))

            tx_ok, tx_data = self.recv_data()

            if tx_ok:
              data = eval(tx_data.decode('UTF-8'))

              if data['success']:
                print('')
                print(SUCCESS_STYLE+data['success_notification']+Style.RESET_ALL)

          
          else:
            # La ficha de mascota no se encuentra registrada. Se notifica el error al usuario.
            print('')
            print(ERROR_STYLE+'[Error] '+data['error_notification']+Style.RESET_ALL)
      
      elif user_option == 3: # Eliminar ficha de mascota
        print(INSTRUCTIONS_STYLE+'Eliminar ficha de mascota'+Style.RESET_ALL)
        print('')
        pet_id = input('Ingresa el ID de la mascota: ')

        # Se genera y envía la transacción para eliminar la ficha de mascota según el ID de mascota ingresado
        data = {'tx_option': 3, 'pet_id': pet_id}

        tx = self.generate_tx(PET_MANAGEMENT_SERVICE_NAME, str(data))

        self.sock.send(tx.encode(encoding='UTF-8'))

        tx_ok, tx_data = self.recv_data()

        if tx_ok:
          data = eval(tx_data.decode('UTF-8'))

          print('')
          if data['success']:
            # La ficha de mascota ha sido eliminada correctamente
            print(SUCCESS_STYLE+data['success_notification']+Style.RESET_ALL)
          
          else:
            # No se ha encontrado una ficha de mascota asociada al ID de mascota ingresado
            print(ERROR_STYLE+'[Error] '+data['error_notification']+Style.RESET_ALL)

      elif user_option == 4: # ======= Volver
        break


      input('\n'+INSTRUCTIONS_STYLE+'Presiona ENTER para continuar'+Style.RESET_ALL)
      clear_screen()
  
  # Método para menú y opciones del servicio de revisiones de mascotas
  def pet_reviews_gui(self):
    # Se instancia el objeto del menú
    menu = ConsoleMenu('Menú de revisiones de mascotas', 'Selecciona una de las opciones a continuación.')
    
    menu.append_item(SelectionItem('Registrar nueva revisión', 0))
    menu.append_item(SelectionItem('Ver detalle de revisiones registradas', 1))
    menu.append_item(SelectionItem('Modificar revisión', 2))
    menu.append_item(SelectionItem('Eliminar revisión', 3))
    menu.append_item(SelectionItem('Volver', 4))

    while True:
      menu.show(False)
      user_option = menu.selected_option

      if user_option == 0: # ============= Registrar nueva revisión
        print(INSTRUCTIONS_STYLE+'Registro de revisión de mascota'+Style.RESET_ALL)
        print('')

        pet_id = input('Ingresa el ID de la mascota: ')

        # Se genera la transacción para validar el ID de la mascota en el servicio de revisiones
        data = {'tx_option': 1, 'tx_sub_option': 1, 'pet_id': pet_id}
        
        tx = self.generate_tx(PET_REVIEWS_SERVICE_NAME, str(data))

        self.sock.send(tx.encode(encoding='UTF-8'))

        tx_ok, tx_data = self.recv_data()

        if tx_ok:
          data = eval(tx_data.decode('UTF-8'))

          if data['pet_exists']:
            # La mascota se encuentra registrada según el ID de mascota ingresado.
            review = {'tx_option': 1 , 'tx_sub_option': 2, 'review_data': {}}

            clear_screen()
            print(INSTRUCTIONS_STYLE+'Datos del propietario'+Style.RESET_ALL)
            print('')
            print('- RUT: '+data['pet_data']['rut_propietario'])
            print('- Nombre: '+data['pet_data']['nombres_propietario']+' '+data['pet_data']['apellidos_propietario'])
            print('')

            print(INSTRUCTIONS_STYLE+'Ficha de la mascota'+Style.RESET_ALL)
            print('')
            print('- Nombre: '+data['pet_data']['nombre'])
            print('- Especie: '+data['pet_data']['especie'])
            print('- Sexo: '+data['pet_data']['sexo'])
            print('- Fecha de nacimiento: '+data['pet_data']['fecha_nacimiento'])
            print('- Raza: '+data['pet_data']['raza'])
            print('- Tamaño: '+data['pet_data']['tamano'])
            print('- Peso (kg): '+str(data['pet_data']['peso']))
            print('- Color: '+data['pet_data']['tamano'])
            print('- Patrón de color: '+data['pet_data']['patron_color'])
            print('- Esterilizado: '+ 'SI' if data['pet_data']['esterilizado'] else 'NO')
            print('- Residencia: '+data['pet_data']['residencia'])

            print('')
            print(INSTRUCTIONS_STYLE+'Formulario de revisión'+Style.RESET_ALL)
            print(INSTRUCTIONS_STYLE+'A continuación, rellena el formulario de la revisión a registrar.'+Style.RESET_ALL)
            print('')
            print(WARNING_STYLE+'* La fecha y hora de revisión serán registradas automáticamente.'+Style.RESET_ALL)
            print('')

            print('- Motivo de revisión (Escribe "END" para salir del campo de texto): ')
            print('')

            motivo_revision = ''
            line = ''
            while True:
              line = input('> ')

              if line == 'END':
                break

              motivo_revision += line + '\n'
            
            review['review_data']['motivo_revision'] = replace_last(motivo_revision, '\n', '')

            print('')
            print('- Diagnóstico (Escribe "END" para salir del campo de texto): ')
            print('')

            diagnostico = ''
            line = ''
            while True:
              line = input('> ')

              if line == 'END':
                break

              diagnostico += line + '\n'
            
            review['review_data']['diagnostico'] = replace_last(diagnostico, '\n', '')

            # Se adjunta los demás datos
            review['review_data']['id_mascota'] = pet_id
            review['review_data']['rut_veterinario'] = self.session['user_data']['rut']
            review['review_data']['fecha_revision'] = str(datetime.now().replace(microsecond=0))

            print('')
            print(INSTRUCTIONS_STYLE+'Resumen de revisión'+Style.RESET_ALL)
            print('')

            print('- ID de mascota: '+str(review['review_data']['id_mascota']))
            print('- RUT de veterinario: '+review['review_data']['rut_veterinario'])
            print('- Fecha de la revisión: '+review['review_data']['fecha_revision'])
            print('- Motivo de la revisión:')
            print('')
            print('.............................................................................................................')
            print('')
            print(review['review_data']['motivo_revision'])
            print('')
            print('.............................................................................................................')
            print('')
            print('- Diagnóstico:')
            print('')
            print('.............................................................................................................')
            print('')
            print(review['review_data']['diagnostico'])
            print('')
            print('.............................................................................................................')
            print('')
          
            conf_op = input('¿Deseas registrar la revisión en la ficha de la mascota? [S/N]: ')

            while conf_op.lower() not in ['s', 'n']:
              conf_op = input('¿Deseas registrar la revisión en la ficha de la mascota? [S/N]: ')
            
            if conf_op.lower() == 's':
              # Se confirma el formulario de revisión y se envía al servicio para registrarlo
              tx = self.generate_tx(PET_REVIEWS_SERVICE_NAME, str(review))

              self.sock.send(tx.encode(encoding='UTF-8'))

              tx_ok, tx_data = self.recv_data()

              if tx_ok:
                data = eval(tx_data.decode('UTF-8'))

                if data['success']:
                  print('')
                  print(SUCCESS_STYLE+data['success_notification']+Style.RESET_ALL)

          else:
            # La mascota no se encuentra registrada.
            print('')
            print(ERROR_STYLE+'[Error] '+data['error_notification']+Style.RESET_ALL)
      
      elif user_option == 1: # ============= Ver detalle de revisiones registradas
        print(INSTRUCTIONS_STYLE+'Detalles de revisiones registradas'+Style.RESET_ALL)
        print('')

        pet_id = input('Ingresa el ID de la mascota: ')

        # Se genera la transacción para validar el ID de la mascota en el servicio de revisiones
        data = {'tx_option': 2, 'tx_sub_option': 1, 'pet_id': pet_id}
        
        tx = self.generate_tx(PET_REVIEWS_SERVICE_NAME, str(data))

        self.sock.send(tx.encode(encoding='UTF-8'))

        tx_ok, tx_data = self.recv_data()

        if tx_ok:
          data = eval(tx_data.decode('UTF-8'))

          if data['pet_exists']:
            # La ficha de mascota se encuentra registrada.
            
            # Se muestran las revisiones disponibles y se notifica en caso de que no tenga.
            if len(data['review_list']) != 0:
              review_table = PrettyTable()
              review_id_list = [] # Lista para almacenar los IDs de revisiones pertenecientes a la mascota consultada.

              # Se agregan las columnas, según los atributos recibidos.
              review_table.field_names = list(data['review_list'][0].keys())
                
              # Se agregan las filas en la tabla según cada usuario registrado
              for review in data['review_list']:
                # Se transforma el diccionario en una lista con los valores de la información del usuario.
                review_table.add_row(list(review.values()))
                review_id_list.append(str(review['id']))
              
              clear_screen()
              print(INSTRUCTIONS_STYLE+'Lista de revisiones disponibles'+Style.RESET_ALL)
              print(INSTRUCTIONS_STYLE+'A continuación, ingresa el ID de la revisión que deseas consultar.'+Style.RESET_ALL)
              print('')
              # Se imprime en la terminal la tabla generada.
              print(review_table)
              print('')
              review_id = input('- ID de revisión: ')

              while review_id not in review_id_list:
                review_id = input('- ID de revisión: ')
              
              # Se envía el ID de revisión seleccionado para obtener el detalle de la revisión
              data = {'tx_option': 2, 'tx_sub_option': 2, 'pet_id': pet_id ,'review_id': review_id}

              tx = self.generate_tx(PET_REVIEWS_SERVICE_NAME, str(data))

              self.sock.send(tx.encode(encoding='UTF-8'))

              tx_ok, tx_data = self.recv_data()

              if tx_ok:
                data = eval(tx_data.decode('UTF-8'))

                if data['success']:
                  clear_screen()
                  print(INSTRUCTIONS_STYLE+'======================== Ficha de la mascota'+Style.RESET_ALL)
                  print('')

                  if data['pet_data']:
                    print('- Nombre: '+data['pet_data']['nombre'])
                    print('- Especie: '+data['pet_data']['especie'])
                    print('- Sexo: '+data['pet_data']['sexo'])
                    print('- Fecha de nacimiento: '+data['pet_data']['fecha_nacimiento'])
                    print('- Raza: '+data['pet_data']['raza'])
                    print('- Tamaño: '+data['pet_data']['tamano'])
                    print('- Peso (kg): '+str(data['pet_data']['peso']))
                    print('- Color: '+data['pet_data']['tamano'])
                    print('- Patrón de color: '+data['pet_data']['patron_color'])
                    print('- Esterilizado: '+ 'SI' if data['pet_data']['esterilizado'] else 'NO')
                    print('- Residencia: '+data['pet_data']['residencia'])
                  
                  else:
                    print(WARNING_STYLE+'* No se ha encontrado la ficha de la mascota según el ID de mascota ingresado.'+Style.RESET_ALL)
                  
                  print('')
                  print(INSTRUCTIONS_STYLE+'======================== Detalle de la revisión'+Style.RESET_ALL)
                  print('')
                  
                  if data['review_data']:
                    print('- ID de mascota: '+str(data['review_data']['id_mascota']))
                    print('- RUT de veterinario: '+data['review_data']['rut_veterinario'])
                    print('- Fecha de la revisión: '+data['review_data']['fecha_revision'])
                    print('- Motivo de la revisión:')
                    print('')
                    print('.............................................................................................................')
                    print('')
                    print(data['review_data']['motivo_revision'])
                    print('')
                    print('.............................................................................................................')
                    print('')
                    print('- Diagnóstico:')
                    print('')
                    print('.............................................................................................................')
                    print('')
                    print(data['review_data']['diagnostico'])
                    print('')
                    print('.............................................................................................................')
                  
                  else:
                    print(WARNING_STYLE+'* No se ha encontrado la revisión de la mascota según el ID de revisión ingresado.'+Style.RESET_ALL)
              
            else:
              print('')
              print(WARNING_STYLE+'* La mascota seleccionada no tiene revisiones registradas.')
          
          else:
            # La ficha de mascota no se encuentra registrada.
            print('')
            print(ERROR_STYLE+'[Error] '+data['error_notification'])

      elif user_option == 4:
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
        self.pet_management_gui()

      elif user_option == 2 and user_data['tipo_usuario'] == 1: # Sección de revisiones de mascotas
        self.pet_reviews_gui()

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
      recv_tx = self.sock.recv(10000)

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
            self.session['user_data'] = user_data
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
