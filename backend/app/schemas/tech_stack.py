from pydantic import BaseModel, RootModel
from typing import Dict, List

class TechStackSearchResult(BaseModel):
    name: str
    category: str
    subcategory: str

class TechStackPreference(RootModel[List[str]]):
    pass

class TechStackRegistry(RootModel[Dict[str, Dict[str, List[str]]]]):
    pass
