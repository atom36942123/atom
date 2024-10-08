# what is atom
Any application has two major parts-backend/frontend. Backend is something that takes time and involves complexity.  
Atom is written to simplify backend development which is common across any product.  
With atom, anyone can deploy ~80% of the backend in ~2 weeks. Atom has gone through rigourus testing that can save a lot of devleopment time.  
After that,further development can be continued without any restriction.  

1. atom has a complete set of pre-built modules that can be used to build production-ready applications in weeks instead of months
2. atom is non opinionated and it was written with no bias for any particular application
3. atom is fully scalable as per need
4. atom follows functional programming paradigm with separation of logic and interface and emphasis on solid principles
5. atom uses objects/datatypes as a fundamental concept with no affection to the type of object thus making it suitable for designing any system.
6. core tech stack = python/fastapi/postgres
7. api docs= https://atom-tbsk.onrender.com/docs

# what type of applications atom can build
1. ecommnerce
2. tinder like apps
3. uber like apps
4. any general saas
5. any social media

# atom core modules

1. auth
2. object level crud
3. rbac
4. admin modules
5. csv uploader
6. redis caching
7. blob storage
8. ai/ml libraries
9. location search
10. master/slave replicas
11. sentry for performance monitoring
12. one click database schema
13. postman collection with automated testing
14. database indexing
15. rate limiter to stop malicious bot activity
16. one click deployment configured using render
    
# vision
1. My vision for atom is to help aspiring entrepreneurs with their technology part so that they can launch/validate faster.
2. Primary motivation is to build as many applications using atom code and help startup founders.
3. you are an aspiring founder, then you can email me to build your tech using atom.
4. email = atom36942@gmail.com
  
# how to run
1. download atom repo
2. create .env file in root folder as per config.py env variable section 
3. install requirements.txt
4. run command=python main.py / fastapi run main.py / fastapi dev main.py

# how to run using docker
1. download atom repo
2. create .env file in root folder as per config.py env variable section 
3. build Dockerfile=docker build . -f Dockerfile.txt -t atomapp
4. run dockerimage=docker run atomapp
