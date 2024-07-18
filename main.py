#server start
from app import app
from function import function_server_start
if __name__=="__main__":
   function_server_start(app,config_backend_host,config_backend_port)

