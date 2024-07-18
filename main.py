#server start
from app import app
from function import function_server_start
if __name__=="__main__":function_server_start(app,"0.0.0.0",8000)
