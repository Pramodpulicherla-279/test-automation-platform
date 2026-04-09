"""
FastAPI routes for MongoDB Jira ticket operations.

Add this to your FastAPI app:

    from fastapi import APIRouter, Query
    from pydantic import BaseModel
    from typing import Optional, List
    from jira_integration.mongo_jira_integration import (
        get_stored_ticket,
        get_all_stored_tickets,
        update_stored_ticket,
        get_ticket_statistics,
        search_stored_tickets
    )
    
    router = APIRouter(prefix="/api/mongodb", tags=["mongodb"])
    
    @router.get("/tickets")
    def get_tickets(
        limit: int = Query(50, ge=1, le=500),
        skip: int = Query(0, ge=0),
        status: Optional[str] = None,
        module: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None
    ):
        tickets = get_all_stored_tickets(
            limit=limit,
            skip=skip,
            status=status,
            module=module,
            priority=priority,
            assignee=assignee
        )
        return {
            "success": True,
            "count": len(tickets),
            "data": tickets
        }
    
    @router.get("/tickets/{issue_id}")
    def get_ticket_by_id(issue_id: str):
        ticket = get_stored_ticket(issue_id)
        if not ticket:
            return {
                "success": False,
                "error": f"Ticket {issue_id} not found"
            }
        return {
            "success": True,
            "data": ticket
        }
    
    @router.get("/statistics")
    def get_stats():
        stats = get_ticket_statistics()
        return {
            "success": True,
            "data": stats
        }
    
    @router.get("/search")
    def search_tickets(q: str = Query(..., min_length=1)):
        results = search_stored_tickets(q)
        return {
            "success": True,
            "count": len(results),
            "data": results
        }
    
    @router.put("/tickets/{issue_id}")
    def update_ticket(issue_id: str, update_data: dict):
        ticket = update_stored_ticket(issue_id, **update_data)
        if not ticket:
            return {
                "success": False,
                "error": f"Ticket {issue_id} not found"
            }
        return {
            "success": True,
            "data": ticket
        }
    
    # Add router to app:
    # app.include_router(router)
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from jira_integration.mongo_jira_integration import (
    get_stored_ticket,
    get_all_stored_tickets,
    update_stored_ticket,
    get_ticket_statistics,
    search_stored_tickets
)


# ─────────────────────────────
# Pydantic Models
# ─────────────────────────────

class TicketUpdate(BaseModel):
    """Model for updating a ticket"""
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    comment: Optional[str] = None
    module: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "In Progress",
                "priority": "Critical",
                "assignee": "Ram"
            }
        }


# ─────────────────────────────
# Router
# ─────────────────────────────

router = APIRouter(
    prefix="/api/mongodb",
    tags=["MongoDB Tickets"]
)


# ─────────────────────────────
# GET Endpoints
# ─────────────────────────────

@router.get("/tickets", response_model=Dict[str, Any])
async def get_tickets(
    limit: int = Query(50, ge=1, le=500, description="Max results to return"),
    skip: int = Query(0, ge=0, description="Number of results to skip"),
    status: Optional[str] = Query(None, description="Filter by status"),
    module: Optional[str] = Query(None, description="Filter by module"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assignee: Optional[str] = Query(None, description="Filter by assignee")
):
    """
    Get all stored Jira tickets from MongoDB.
    
    Query Parameters:
    - limit: Max results (1-500, default 50)
    - skip: Pagination offset (default 0)
    - status: Filter by status (Open, In Progress, Done, etc.)
    - module: Filter by module (Onboarding, Authentication, etc.)
    - priority: Filter by priority (Low, Medium, High, Critical)
    - assignee: Filter by assignee name
    """
    try:
        tickets = get_all_stored_tickets(
            limit=limit,
            skip=skip,
            status=status,
            module=module,
            priority=priority,
            assignee=assignee
        )
        
        return {
            "success": True,
            "count": len(tickets),
            "data": tickets
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving tickets: {str(e)}"
        )


@router.get("/tickets/{issue_id}", response_model=Dict[str, Any])
async def get_ticket_by_id(issue_id: str):
    """
    Get a specific ticket by Jira issue ID.
    
    Parameters:
    - issue_id: Jira issue key (e.g., "AT-87")
    """
    try:
        ticket = get_stored_ticket(issue_id)
        
        if not ticket:
            raise HTTPException(
                status_code=404,
                detail=f"Ticket {issue_id} not found"
            )
        
        return {
            "success": True,
            "data": ticket
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving ticket: {str(e)}"
        )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_stats():
    """Get statistics about stored tickets"""
    try:
        stats = get_ticket_statistics()
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting statistics: {str(e)}"
        )


@router.get("/search", response_model=Dict[str, Any])
async def search_tickets(q: str = Query(..., min_length=1, description="Search query")):
    """
    Search tickets by text.
    
    Searches in: summary, description, module, feature, test_name
    
    Parameters:
    - q: Search query (minimum 1 character)
    """
    try:
        results = search_stored_tickets(q)
        
        return {
            "success": True,
            "count": len(results),
            "data": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching tickets: {str(e)}"
        )


# ─────────────────────────────
# PUT Endpoints
# ─────────────────────────────

@router.put("/tickets/{issue_id}", response_model=Dict[str, Any])
async def update_ticket(issue_id: str, update_data: TicketUpdate):
    """
    Update a ticket in MongoDB.
    
    Parameters:
    - issue_id: Jira issue key (e.g., "AT-87")
    - update_data: Fields to update (status, priority, assignee, etc.)
    """
    try:
        # Only include non-None fields
        updates = {k: v for k, v in update_data.dict().items() if v is not None}
        
        if not updates:
            raise HTTPException(
                status_code=400,
                detail="No fields to update"
            )
        
        ticket = update_stored_ticket(issue_id, **updates)
        
        if not ticket:
            raise HTTPException(
                status_code=404,
                detail=f"Ticket {issue_id} not found"
            )
        
        return {
            "success": True,
            "data": ticket,
            "message": f"Ticket {issue_id} updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating ticket: {str(e)}"
        )


# ─────────────────────────────
# Health Check
# ─────────────────────────────

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Check if MongoDB connection is healthy"""
    from jira_integration.mongo_config import is_mongodb_enabled
    
    return {
        "success": True,
        "mongodb_enabled": is_mongodb_enabled(),
        "message": "MongoDB API is ready"
    }