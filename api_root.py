#root api
@app.get("/")
async def function_root():
   return {"status":1,"message":f"welcome to {[*postgres_object_dict]}"}
