from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

CATEGORIES = ['Еда', 'Транспорт', 'Жильё', 'Развлечения', 'Здоровье', 'Образование', 'Шопинг', 'Прочее']
CategoryName = Literal['Еда', 'Транспорт', 'Жильё', 'Развлечения', 'Здоровье', 'Образование', 'Шопинг', 'Прочее']

class Classification(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: int
    category: CategoryName

class Classifications(BaseModel):
    model_config = ConfigDict(extra='forbid')
    items: list[Classification]

class Insight(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: str
    text: str

class Insights(BaseModel):
    model_config = ConfigDict(extra='forbid')
    observations: list[Insight]
    tips: list[Insight]

class ChatRequest(BaseModel):
    month: str = Field(pattern=r'^\d{4}-\d{2}$')
    message: str = Field(min_length=1, max_length=1000)
