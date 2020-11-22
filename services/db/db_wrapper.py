import mysql.connector

class Database:
  def __init__(self, host, port, user, passwd, database, autocommit=True):
    self.host = host
    self.port = port
    self.user = user
    self.passwd = passwd
    self.database = database
    self.autocommit = autocommit

    self.connect()
  
  def connect(self):
    try:
      self.db = mysql.connector.connect(host=self.host,
                                        port=self.port,
                                        user=self.user,
                                        passwd=self.passwd,
                                        database=self.database,
                                        autocommit=self.autocommit)
                            
      self.cursor = self.db.cursor(dictionary=True, buffered=True)
      self.cursor.execute('SET NAMES utf8mb4;')
    
    except Exception as error:
      print(error)
      return
  
  def query(self, query, values):
    try:
      self._query(query, values)
    
    except (mysql.connector.errors.InterfaceError, mysql.connector.errors.OperationalError):
      self.connect()
      self._query(query, values)
    
    return self.cursor
  
  def _query(self, query, values):
    if values:
      self.cursor.execute(query, values)
    else:
      self.cursor.execute(query)
  

  
