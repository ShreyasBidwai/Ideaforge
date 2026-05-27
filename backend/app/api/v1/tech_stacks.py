from fastapi import APIRouter, Depends, Query
from typing import Dict, List, Optional
from app.api.deps import get_current_user
from app.core.tech_stacks import TECH_STACK_REGISTRY
from app.schemas.tech_stack import TechStackRegistry, TechStackSearchResult

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.get("", response_model=TechStackRegistry)
async def get_tech_stacks():
    return TECH_STACK_REGISTRY

@router.get("/search", response_model=List[TechStackSearchResult])
async def search_tech_stacks(q: Optional[str] = Query(default="")):
    if not q:
        return []
    
    results = []
    query = q.lower()
    for category, subcats in TECH_STACK_REGISTRY.items():
        for subcat, items in subcats.items():
            for item in items:
                if query in item.lower():
                    results.append({
                        "name": item,
                        "category": category,
                        "subcategory": subcat
                    })
    return results

@router.get("/categories", response_model=Dict[str, List[str]])
async def get_categories():
    return {category: list(subcats.keys()) for category, subcats in TECH_STACK_REGISTRY.items()}
