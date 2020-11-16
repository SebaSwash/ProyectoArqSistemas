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
import socket, argparse

# Constantes con nombres de servicios a utilizar


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
  def generate_tx(self, service,data):
    return self.generate_tx_length(len(service + data)) + service + data
  
  # Método para dividir la transacción recibida desde el servidor y separarla para verificar estado (OK/NK)
  def split_recv_tx(self,tx):
    tx_length = tx[:5] # Largo de la transacción
    tx_service = tx[5:10] # Servicio invocado
    tx_status = tx[10:12] # 'OK' (éxito) o 'NK' (fallido)
    tx_data = tx[12:] # Data recibida desde el servidor

    return (tx_length, tx_service, tx_status, tx_data)
  
  def run(self):
    print('Ejecución del cliente . . .')

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
