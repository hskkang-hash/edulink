"""
留덉씠洹몃젅?댁뀡 ?앹꽦 ?ㅽ겕由쏀듃
"""
from flask import Flask
from flask_migrate import Migrate
from models import db
import os
import sys

# Flask ???앹꽦 諛??ㅼ젙
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///./edulinks.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db 珥덇린??
db.init_app(app)

# Flask-Migrate 珥덇린??(CLI commands ?쒖꽦??
migrate = Migrate(app, db)

if __name__ == '__main__':
    # 留덉씠洹몃젅?댁뀡 ?앹꽦
    os.environ['FLASK_APP'] = 'create_migration.py'
    
    with app.app_context():
        print("珥덇린 留덉씠洹몃젅?댁뀡???앹꽦?섎뒗 以?..")
        try:
            # alembic??吏곸젒 ?ъ슜?섏뿬 留덉씠洹몃젅?댁뀡 ?앹꽦
            from alembic.config import Config as AlembicConfig
            from alembic import command
            
            alembic_cfg = AlembicConfig('migrations/alembic.ini')
            alembic_cfg.set_main_option('script_location', 'migrations')
            alembic_cfg.set_main_option('sqlalchemy.url', app.config['SQLALCHEMY_DATABASE_URI'])
            
            # 留덉씠洹몃젅?댁뀡 ?앹꽦
            command.revision(alembic_cfg, autogenerate=True, message='Initial migration: create all tables')
            print("??Initial migration created successfully")
        except Exception as e:
            print(f"??留덉씠洹몃젅?댁뀡 ?앹꽦 ?ㅽ뙣: {e}")
            sys.exit(1)

