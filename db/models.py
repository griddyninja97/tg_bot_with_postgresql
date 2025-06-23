from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    photos = relationship("Photo", back_populates="group", cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    file_id = Column(String, nullable=False)

    group_id = Column(Integer, ForeignKey("groups.id"))
    group = relationship("Group", back_populates="photos")
