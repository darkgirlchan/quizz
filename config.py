# config.py
class Config:
    # Configuración de SQL Server para la base de datos quizz
    SQLALCHEMY_DATABASE_URI = 'mssql+pyodbc://@DARKSYSTEM/quizz?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'tu_clave_secreta_aqui'