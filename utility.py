#router
from fastapi import APIRouter
router=APIRouter(tags=["utility"])

#pcache
from fastapi import Request
from fastapi_cache.decorator import cache
@router.get("/{x}/utility/pcache")
@cache(expire=60)
async def function_utility_pcache(request:Request): 
   #logic
   config_pcache={
   "user_count":"select count(*) from users;"
   }
   temp={}
   for k,v in config_pcache.items():
      query=v
      values={}
      output=await request.state.postgres_object.fetch_all(query=query,values=values)
      if "count" in k:temp[k]=output[0]["count"]
      else:temp[k]=output
   #final
   return {"status":1,"message":temp}
