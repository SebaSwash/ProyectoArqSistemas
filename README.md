# ProyectoArqSistemas
Proyecto semestral SOA - Arquitectura de Sistemas (02 - 2020)
---
### Integrantes
* Lorenzo Alfaro Bravo
* Flor Calla Lazo
* Sebastián Toro Severino

---
## Lista de servicios disponibles

| Servicio                  | Descripción                                                                                                                                                                  | Nombre del archivo     | Argumentos necesarios                                | Observaciones                                                              |
|---------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------|------------------------------------------------------|----------------------------------------------------------------------------|
| Autenticación de usuarios | Servicio para realizar la autenticación de usuarios (inicio de sesión).                                                                                                      | user_authentication.py | host - port (numérico) - service_name (5 caracteres) | Finalizado.                                                                |
| Gestión de usuarios       | Servicio para funcionalidades de gestión o administración de usuarios, tales como registro de usuarios, modificación, eliminación, listado de usuarios y detalle de usuario. | user_management.py     | host - port (numérico) - service_name (5 caracteres) | Finalizado (Falta revisar detalle al enviar lista de usuarios por tamaño máximo soportado por el socket). |
| Gestión de mascotas       | Servicio para funcionalidades de gestión o administración de mascotas, tales como registro de fichas de mascotas, modificación, eliminación, y detalle de fichas. | pet_management.py     | host - port (numérico) - service_name (5 caracteres) | Finalizado (Para revisión). |
