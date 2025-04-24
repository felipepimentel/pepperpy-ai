"""
API routes for todos.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Body
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/workflows/{workflow_id}/todos", tags=["todos"])

# Pydantic models for request/response validation
class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    completed: bool = False

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    completed: Optional[bool] = None

class TodoResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    priority: str
    completed: bool
    created_at: str
    workflow_id: str

# In-memory storage for todos (for demo purposes)
# In a real app, this would be a database
todos_db: Dict[str, List[TodoResponse]] = {}

@router.get("/", response_model=List[TodoResponse])
async def get_todos(workflow_id: str = Path(..., description="The ID of the workflow")):
    """
    Get all todos for a specific workflow.
    """
    if workflow_id not in todos_db:
        todos_db[workflow_id] = []
    
    return todos_db[workflow_id]

@router.post("/", response_model=TodoResponse)
async def create_todo(
    workflow_id: str = Path(..., description="The ID of the workflow"),
    todo: TodoCreate = Body(..., description="The todo to create")
):
    """
    Create a new todo for a specific workflow.
    """
    # Ensure workflow exists in our db
    if workflow_id not in todos_db:
        todos_db[workflow_id] = []
    
    # Create new todo
    new_todo = TodoResponse(
        id=str(uuid.uuid4()),
        title=todo.title,
        description=todo.description,
        priority=todo.priority,
        completed=todo.completed,
        created_at=datetime.now().isoformat(),
        workflow_id=workflow_id
    )
    
    # Add to in-memory database
    todos_db[workflow_id].append(new_todo)
    
    return new_todo

@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    workflow_id: str = Path(..., description="The ID of the workflow"),
    todo_id: str = Path(..., description="The ID of the todo")
):
    """
    Get a specific todo by ID.
    """
    if workflow_id not in todos_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    for todo in todos_db[workflow_id]:
        if todo.id == todo_id:
            return todo
    
    raise HTTPException(status_code=404, detail="Todo not found")

@router.patch("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    workflow_id: str = Path(..., description="The ID of the workflow"),
    todo_id: str = Path(..., description="The ID of the todo"),
    todo_update: TodoUpdate = Body(..., description="The todo updates")
):
    """
    Update a specific todo by ID.
    """
    if workflow_id not in todos_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    for i, todo in enumerate(todos_db[workflow_id]):
        if todo.id == todo_id:
            # Update fields if provided
            update_data = todo_update.dict(exclude_unset=True)
            updated_todo = todos_db[workflow_id][i].copy()
            
            for field, value in update_data.items():
                setattr(updated_todo, field, value)
            
            todos_db[workflow_id][i] = updated_todo
            return updated_todo
    
    raise HTTPException(status_code=404, detail="Todo not found")

@router.delete("/{todo_id}", response_model=Dict[str, str])
async def delete_todo(
    workflow_id: str = Path(..., description="The ID of the workflow"),
    todo_id: str = Path(..., description="The ID of the todo")
):
    """
    Delete a specific todo by ID.
    """
    if workflow_id not in todos_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    for i, todo in enumerate(todos_db[workflow_id]):
        if todo.id == todo_id:
            # Remove todo from list
            todos_db[workflow_id].pop(i)
            return {"status": "success", "message": "Todo deleted successfully"}
    
    raise HTTPException(status_code=404, detail="Todo not found")

@router.delete("/", response_model=Dict[str, str])
async def delete_all_todos(workflow_id: str = Path(..., description="The ID of the workflow")):
    """
    Delete all todos for a specific workflow.
    """
    if workflow_id in todos_db:
        todos_db[workflow_id] = []
    
    return {"status": "success", "message": "All todos deleted successfully"} 