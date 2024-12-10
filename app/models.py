from sqlalchemy import Column, Integer, String
from app.database import Base

# Define the User class from Base
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    zitadel_id = Column(String(256))
    email = Column(String(256))
    device_id = Column(String(256), default=None)
    device_username = Column(String(256), default=None)
    pin = Column(String(12), default=None)
