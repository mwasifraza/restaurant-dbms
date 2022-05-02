from flask import Flask, session
from flask_bcrypt import Bcrypt
from datetime import datetime
# from flask_login import LoginManager
import pyodbc
#APP
app = Flask(__name__)
app.config['SECRET_KEY'] = 'key is wasif'
bcrypt = Bcrypt(app)
# login_manager = LoginManager(app)
current_date = datetime.today().strftime('%D')
#DATABASE CONNECTION
driver = "{ODBC DRIVER 17 for SQL SERVER}"
server = "DESKTOP-65BV9CJ\SQLEXPRESS"
database = "restaurantdb"
conc = "yes"

conn = pyodbc.connect("Driver="+driver+"; SERVER="+server+"; DATABASE="+database+"; Trusted_Connection="+conc)
cursor = conn.cursor()

#LOGIN CHECK
def user_login():
  if 'loggedin' in session:
      return True
  else:
      return False
#ROUTES
from foodfusion import routes