#import
from fastapi.middleware.cors import CORSMiddleware

#config
cors_origins=["*"]
cors_credentials=True
cors_method=["*"]
cors_header=["*"]

#logic
app.add_middleware(
  CORSMiddleware,allow_origins=cors_origins,
  allow_credentials=cors_credentials,
  allow_methods=cors_method,allow_headers=cors_header
)
