# about
```
1. an open-source backend framework for faster development
2. entire codebase is in a single file, main.py
3. combines procedural and functional programming
4. procedures ensures better global/local state access
5. functions ensures deterministic behavior of the code
6. follows SOLID principles
7. supports high-performance application development
8. uses realtional dataabse at its core
9. Reduces repetitive work with reusable modules
10. Enables rapid iteration and faster go-to-market
11. Built with Python,FastAPI,PostgreSQL,Redis,Kafka,Rabbitmq,Mongodb
12. Uses raw SQL for optimized queries and better control
13. Supports high-throughput pipelines via RabbitMQ, LavinMQ, or Kafka
14. Provides object-level CRUD operations by directly interacting with database schema
15. Auto-generates entire business database schemas from a single JSON config
16. ex. build a linkedIn-like backend in 2-3 weeks
```

# modules
```
1. authentication module
2. endpoints for authenticated users
3. direct crud apis on database objects
4. role-based access control for admin operations
5. built-in apis for aws services like s3,ses,sns 
6. deploy instantly using render
7. privileged access for root users 
8. import large datasets via csv 
9. improve performance with redis caching
10. kafka, rabbitmq, lavinmq, redis pub-sub
11. prevent api abuse with request limiting 
12. auto-generate database schemas via api 
13. background task execution 
14. scale with read database replication  
15. use mongodb as a secondary database
16. soft/hard delete on object level
```

# how to run
```
1. download atom repo
2. install requirements.txt
3. create .env file
4. run = python main.py
5. run with reload =  uvicorn main:app --reload
```

# how to run using docker
```
1. docker build -t atom .
2. docker run -p 8000:8000 atom
```

# curl testing
```
1. add .env key=baseurl,token_root,token_admin,file_create,file_update,file_delete,test_id
2. chmod +x curl.sh
3. ./curl.sh
```

# api docs
```
https://www.atom42.org/docs
```

# contact
```
Have an idea! Want to build affordable and scalable tech. 
email @ atom36942@gmail.com
```