from utils.database import Base
from sqlalchemy.schema import Column
from sqlalchemy.types import Text, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
import pytz
from datetime import datetime


class SpeechResult(Base):
    __tablename__ = "speech_result"

    id = Column(Integer, primary_key=True, index=True)
    input_file_audio = Column(Text)
    output_file_audio = Column(Text)
    speech_to_text = Column(Text, nullable=False)
    ai_generated = Column(Text, nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(
            pytz.timezone('Asia/Jakarta')
        ).replace(tzinfo=None),
        nullable=False
    )
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship('User', back_populates='speech_result')
