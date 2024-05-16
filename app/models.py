from sqlalchemy import Column, Integer, String
from .database import Base

# Example table model
class ExampleTable(Base):
    __tablename__ = "example_table"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)

