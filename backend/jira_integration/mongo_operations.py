"""
jira_integration/mongo_operations.py
────────────────────────────────────
Database operations for storing and retrieving Jira automation tickets.

Usage:
    from jira_integration.mongo_operations import save_ticket, get_ticket, get_all_tickets
    
    # Save a ticket
    ticket_data = {
        "issue_id": "AT-87",
        "summary": "Test failed",
        "module": "Onboarding",
        ...
    }
    result = save_ticket(ticket_data)
    
    # Get a ticket
    ticket = get_ticket("AT-87")
    
    # Get all tickets
    tickets = get_all_tickets(limit=10, status="Open")
"""

from jira_integration.mongo_config import get_tickets_collection, is_mongodb_enabled
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid
import logging

logger = logging.getLogger("uvicorn.error")


def _generate_ticket_id() -> str:
    """Generate a unique ticket ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"{timestamp}-{unique_id}"


def save_ticket(
    issue_id: str,
    summary: str,
    module: str,
    feature: str,
    app_name: Optional[str] = None,
    app_version: Optional[str] = None,
    description: Optional[str] = None,
    test_name: Optional[str] = None,
    test_id: Optional[str] = None,
    steps_executed: Optional[List[str]] = None,
    developer_name: Optional[str] = None,
    priority: str = "High",
    labels: Optional[List[str]] = None,
    assignee: Optional[str] = None,
    status: str = "Open",
    environment: str = "staging",
    start_date: Optional[str] = None,
    due_date: Optional[str] = None,
    **extra_fields
) -> Optional[str]:
    """
    Save a Jira ticket to MongoDB.
    
    Args:
        issue_id: Jira issue key (e.g., "AT-87")
        summary: Issue title
        module: Module name (Onboarding, Authentication, etc.)
        feature: Feature name
        app_name: Application name
        app_version: Application version
        description: Detailed description
        test_name: Name of the test
        test_id: Test ID
        steps_executed: List of steps executed
        developer_name: Developer name
        priority: Issue priority (Low, Medium, High, Critical)
        labels: List of labels
        assignee: Assignee name
        status: Issue status (Open, In Progress, Done, etc.)
        environment: Environment (dev, staging, production)
        start_date: Start date (ISO format)
        due_date: Due date (ISO format)
        **extra_fields: Any additional fields
    
    Returns:
        Ticket ID if saved successfully, None otherwise
    """
    
    if not is_mongodb_enabled():
        logger.warning("[MongoDB] MongoDB is not connected. Ticket not saved.")
        return None
    
    try:
        collection = get_tickets_collection()
        if collection is None:
            logger.error("[MongoDB] Could not get tickets collection")
            return None
        
        # Generate internal ticket ID
        ticket_id = _generate_ticket_id()
        
        # Build ticket document
        ticket_doc = {
            "ticket_id": ticket_id,
            "issue_id": issue_id,
            "summary": summary,
            "module": module,
            "feature": feature,
            "app_name": app_name or "Unknown",
            "app_version": app_version or "Unknown",
            "description": description or "",
            "test_name": test_name or "Unknown Test",
            "test_id": test_id or "Unknown",
            "steps_executed": steps_executed or [],
            "developer_name": developer_name or "Unknown",
            "priority": priority,
            "labels": labels or [],
            "assignee": assignee or "Unassigned",
            "status": status,
            "environment": environment,
            "start_date": start_date or datetime.now().isoformat(),
            "due_date": due_date,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            **extra_fields
        }
        
        # Try to insert
        result = collection.insert_one(ticket_doc)
        
        logger.info(f"[MongoDB] ✓ Ticket saved: {issue_id} (ID: {ticket_id})")
        return ticket_id
        
    except Exception as e:
        logger.error(f"[MongoDB] ✗ Error saving ticket: {str(e)}")
        return None


def get_ticket(issue_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a ticket by issue ID.
    
    Args:
        issue_id: Jira issue key (e.g., "AT-87")
    
    Returns:
        Ticket data if found, None otherwise
    """
    
    if not is_mongodb_enabled():
        return None
    
    try:
        collection = get_tickets_collection()
        if collection is None:
            return None
        
        ticket = collection.find_one({"issue_id": issue_id})
        
        if ticket:
            # Convert MongoDB ObjectId to string
            ticket["_id"] = str(ticket.get("_id"))
            logger.info(f"[MongoDB] Retrieved ticket: {issue_id}")
            return ticket
        else:
            logger.info(f"[MongoDB] Ticket not found: {issue_id}")
            return None
            
    except Exception as e:
        logger.error(f"[MongoDB] Error retrieving ticket: {str(e)}")
        return None


def get_all_tickets(
    limit: int = 50,
    skip: int = 0,
    status: Optional[str] = None,
    module: Optional[str] = None,
    priority: Optional[str] = None,
    assignee: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: int = -1
) -> List[Dict[str, Any]]:
    """
    Retrieve all tickets with optional filters.
    
    Args:
        limit: Maximum number of tickets to return
        skip: Number of tickets to skip (for pagination)
        status: Filter by status
        module: Filter by module
        priority: Filter by priority
        assignee: Filter by assignee
        sort_by: Field to sort by
        sort_order: Sort order (1 for ascending, -1 for descending)
    
    Returns:
        List of tickets
    """
    
    if not is_mongodb_enabled():
        return []
    
    try:
        collection = get_tickets_collection()
        if collection is None:
            return []
        
        # Build filter
        filter_dict = {}
        if status:
            filter_dict["status"] = status
        if module:
            filter_dict["module"] = module
        if priority:
            filter_dict["priority"] = priority
        if assignee:
            filter_dict["assignee"] = assignee
        
        # Query
        tickets = list(
            collection.find(filter_dict)
            .sort(sort_by, sort_order)
            .skip(skip)
            .limit(limit)
        )
        
        # Convert ObjectIds
        for ticket in tickets:
            ticket["_id"] = str(ticket.get("_id"))
        
        logger.info(f"[MongoDB] Retrieved {len(tickets)} tickets")
        return tickets
        
    except Exception as e:
        logger.error(f"[MongoDB] Error retrieving tickets: {str(e)}")
        return []


def update_ticket(
    issue_id: str,
    **update_fields
) -> Optional[Dict[str, Any]]:
    """
    Update a ticket by issue ID.
    
    Args:
        issue_id: Jira issue key
        **update_fields: Fields to update
    
    Returns:
        Updated ticket data if successful, None otherwise
    """
    
    if not is_mongodb_enabled():
        return None
    
    try:
        collection = get_tickets_collection()
        if collection is None:
            return None
        
        # Add updated_at timestamp
        update_fields["updated_at"] = datetime.now().isoformat()
        
        result = collection.find_one_and_update(
            {"issue_id": issue_id},
            {"$set": update_fields},
            return_document=True
        )
        
        if result:
            result["_id"] = str(result.get("_id"))
            logger.info(f"[MongoDB] Updated ticket: {issue_id}")
            return result
        else:
            logger.warning(f"[MongoDB] Ticket not found for update: {issue_id}")
            return None
            
    except Exception as e:
        logger.error(f"[MongoDB] Error updating ticket: {str(e)}")
        return None


def delete_ticket(issue_id: str) -> bool:
    """
    Delete a ticket by issue ID.
    
    Args:
        issue_id: Jira issue key
    
    Returns:
        True if deleted, False otherwise
    """
    
    if not is_mongodb_enabled():
        return False
    
    try:
        collection = get_tickets_collection()
        if collection is None:
            return False
        
        result = collection.delete_one({"issue_id": issue_id})
        
        if result.deleted_count > 0:
            logger.info(f"[MongoDB] Deleted ticket: {issue_id}")
            return True
        else:
            logger.warning(f"[MongoDB] Ticket not found for deletion: {issue_id}")
            return False
            
    except Exception as e:
        logger.error(f"[MongoDB] Error deleting ticket: {str(e)}")
        return False


def get_statistics() -> Dict[str, Any]:
    """
    Get statistics about stored tickets.
    
    Returns:
        Statistics dictionary
    """
    
    if not is_mongodb_enabled():
        return {}
    
    try:
        collection = get_tickets_collection()
        if collection is None:
            return {}
        
        total = collection.count_documents({})
        
        # Group by status
        by_status = list(collection.aggregate([
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]))
        
        # Group by priority
        by_priority = list(collection.aggregate([
            {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
        ]))
        
        # Group by module
        by_module = list(collection.aggregate([
            {"$group": {"_id": "$module", "count": {"$sum": 1}}}
        ]))
        
        # Group by assignee
        by_assignee = list(collection.aggregate([
            {"$group": {"_id": "$assignee", "count": {"$sum": 1}}}
        ]))
        
        return {
            "total": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "by_module": by_module,
            "by_assignee": by_assignee
        }
        
    except Exception as e:
        logger.error(f"[MongoDB] Error getting statistics: {str(e)}")
        return {}


def search_tickets(query: str, fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Search tickets by text.
    
    Args:
        query: Search query string
        fields: Fields to search in (default: summary, description, module, feature)
    
    Returns:
        List of matching tickets
    """
    
    if not is_mongodb_enabled():
        return []
    
    try:
        collection = get_tickets_collection()
        if collection is None:
            return []
        
        if not fields:
            fields = ["summary", "description", "module", "feature", "test_name"]
        
        # Build regex search filter
        regex_query = {"$regex": query, "$options": "i"}
        filter_dict = {"$or": [{field: regex_query} for field in fields]}
        
        tickets = list(collection.find(filter_dict).limit(50))
        
        # Convert ObjectIds
        for ticket in tickets:
            ticket["_id"] = str(ticket.get("_id"))
        
        logger.info(f"[MongoDB] Found {len(tickets)} tickets matching '{query}'")
        return tickets
        
    except Exception as e:
        logger.error(f"[MongoDB] Error searching tickets: {str(e)}")
        return []