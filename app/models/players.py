from app.database import Base
from models.matches import Matches
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, String, Integer, Enum, Boolean, List, ForeignKey

class Players(Base):
    __tablename__ = 'players'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_name: Mapped[str] = mapped_column(String(50))
    is_owner: Mapped[bool] = mapped_column(Boolean)
    
    match_id: Mapped[int] = mapped_column(Integer, ForeignKey('matches.id'))
    match: Mapped["Matches"] = relationship("Matches", back_populates="players")
    
    def __repr__(self):
        return (f"Player(id={self.id!r}, player_name={self.player_name!r}, "
                f"is_owner={self.is_owner!r}, match_id={self.match_id!r})")