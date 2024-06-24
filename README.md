# Filestack App for Shopify
## Run 
Setup 
```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
```
Run
```bash
    ngrok http <PORT>
```
create a .env file at the root of the project based on src/template/.env.template and provide the all the env variables.
The ngrok forward urls should also need to updated in .env file. 

```bash
    python3 src/server.py
```


## Build
To build this project run

```bash
  docker compose up --build
```

To setup filestack db
```bash
  docker exec -u root $(docker ps -aqf "name=sqlite") chmod 777 ./data
  docker exec -it $(docker ps -aqf "name=sqlite") sh
  sqlite3 ./data/filestack.db
```

To create the table schema
```bash
    CREATE TABLE shopify_filepicker(

    id integer NOT NULL, 

    shop_domain text NULL, 

    filestack_email text NULL, 

    filestack_apikey text NULL,v

    developer_id integer NULL,

    policy text NULL,

    signature text NULL,

    accept_file text NULL,

    allow_manual_retry integer NULL,

    display_mode integer NULL,

    disable_transformer integer NULL,

    support_email text NULL,

    language text NULL,

    num_retry integer NULL,

    num_concurrency integer NULL,

    cloud_container text NULL,

    cloud_folder text NULL,

    cloud_path text NULL,

    error_timeout text NULL,

    from_sources text NULL,

    max_files integer NULL,

    min_files integer NULL,

    max_size integer NULL,

    max_image_dimension text NULL,

    min_image_dimension text NULL,

    image_dimension text NULL,

    transformation text NULL,

    upload_tags text NULL,

    upload_reports text NULL,

    status text NULL,

    created_at text NULL,

    modified_at text NULL

    );

```