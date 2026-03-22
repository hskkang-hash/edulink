"""
Flask-Migrate 珥덇린???ㅽ겕由쏀듃
留덉씠洹몃젅?댁뀡 ?섍꼍 ?ㅼ젙 諛?珥덇린 留덉씠洹몃젅?댁뀡 ?앹꽦
"""
from flask import Flask
from flask_migrate import Migrate, init, migrate as create_migration
from models import db
import os

# Flask ???ㅼ젙
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///./edulinks.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db 珥덇린??
db.init_app(app)

# Flask-Migrate 珥덇린??
migrate_obj = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        # 留덉씠洹몃젅?댁뀡 ?대뜑媛 ?놁쑝硫??앹꽦
        if not os.path.exists('migrations'):
            print("留덉씠洹몃젅?댁뀡 ?섍꼍??珥덇린?뷀븯??以?..")
            init()
            print("??留덉씠洹몃젅?댁뀡 ?대뜑媛 ?앹꽦?섏뿀?듬땲?? migrations/")
            
            # 珥덇린 留덉씠洹몃젅?댁뀡 ?앹꽦
            print("珥덇린 留덉씠洹몃젅?댁뀡???앹꽦?섎뒗 以?..")
            create_migration(message='Initial migration: create all tables')
            print("??Initial migration created successfully")
        else:
            print("留덉씠洹몃젅?댁뀡 ?대뜑媛 ?대? 議댁옱?⑸땲??")

