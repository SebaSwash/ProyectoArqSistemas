# Función para limpiar la pantalla dependiendo del sistema
import os

def clear_screen():
  # Limpieza de pantalla dependiendo del SO
  os.system('cls' if os.name == 'nt' else 'clear')