import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

db_name = os.environ.get('DATABASE')

basedir = os.getcwd()

class DBConfig:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, db_name)
    SQLALCHEMY_TRACK_MODIFICATIONS = False


db = SQLAlchemy()

class ShopifyFilepicker(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    access_token = db.Column(db.String, unique=True, nullable=False)
    shop_domain = db.Column(db.String, nullable=False)
    developer_id = db.Column(db.Integer, nullable=False)            
    filestack_email = db.Column(db.String, nullable=False)
    apikey = db.Column(db.String, nullable=False)   
    policy = db.Column(db.String, default='')
    signature = db.Column(db.String, default='')
    from_sources = db.Column(db.String, default='["local_file_system"]')
    accept_file_types = db.Column(db.String, default='image/*')
    max_filesize = db.Column(db.Integer, default=10000000)
    max_files = db.Column(db.Integer, default=1)
    max_image_dimension = db.Column(db.String, default='')
    image_dimension = db.Column(db.String, default='')
    image_editor = db.Column(db.String, default='Simple')
    transformation_crop = db.Column(db.Boolean, default=False)
    transformation_resize = db.Column(db.Boolean, default=False)
    transformation_rotate = db.Column(db.Boolean, default=False)
    num_retry = db.Column(db.Integer, default=10)
    num_concurrency = db.Column(db.Integer, default=3)
    error_timeout = db.Column(db.Integer, default=120000)
    chunk_size = db.Column(db.Integer, default=1000000)
    part_size = db.Column(db.Integer, default=6000000)
    progress_interval = db.Column(db.Integer, default=1000)
    retry_factor = db.Column(db.Integer,default=2)
    retry_maxtime = db.Column(db.Integer, default=15000)
    display_mode = db.Column(db.String, default='inline')
    language = db.Column(db.String, default='en')
    min_files = db.Column(db.Integer, default=1)
    support_email = db.Column(db.String, default='')
    cloud_container = db.Column(db.String, default='S3')
    cloud_folder = db.Column(db.String, default="")
    cloud_path = db.Column(db.String, default="")
    intigintergrity_check = db.Column(db.Boolean, default=False)
    intelligent = db.Column(db.Boolean, default=False)
    upload_tags = db.Column(db.String, default='')
    allow_manual_retry = db.Column(db.Boolean, default=False)
    disable_transformer = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}