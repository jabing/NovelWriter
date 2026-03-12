from typing import Any

from fastapi import APIRouter, Body, HTTPException

try:
    from Writer.src.agents.orchestrator import AgentOrchestrator
except Exception:
    AgentOrchestrator = None  # type: ignore

router = APIRouter(prefix="/api/agents", tags=["agents"], redirect_slashes=False)

def _get_orchestrator() -> Any:
    if AgentOrchestrator is None:
        raise HTTPException(status_code=500, detail="AgentOrchestrator is unavailable.")
    return AgentOrchestrator()


@router.get("/", response_model=list[str])
async def list_agent_types():
    """
    GET /api/agents
    Return a list of available agent types.
    """
    try:
        orch = _get_orchestrator()
        if hasattr(orch, "get_agent_types"):
            agent_types = orch.get_agent_types()
        elif hasattr(orch, "agent_types"):
            agent_types = list(orch.agent_types)
        else:
            agent_types = ["orchestrator", "plot", "character", "worldbuilding", "editor", "publisher"]
        return [str(t) for t in agent_types]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enumerate agent types: {e}")


@router.get("/{agent_type}/status")
async def get_agent_status(agent_type: str):
    """
    GET /api/agents/{agent_type}/status
    Return the current status of a given agent type.
    """
    try:
        orch = _get_orchestrator()
        if hasattr(orch, "get_status") and callable(orch.get_status):
            status = orch.get_status(agent_type)
        elif getattr(orch, "status_of", None) and callable(orch.status_of):
            status = orch.status_of(agent_type)
        else:
            status = {"agent_type": agent_type, "status": "unknown"}
        return status
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not get status for '{agent_type}': {e}")


@router.post("/{agent_type}/execute")
async def execute_agent(agent_type: str, payload: dict[str, Any] = Body(..., embed=True)):
    """
    POST /api/agents/{agent_type}/execute
    Execute an action for a given agent type with optional payload.
    Example body:
    {
      "prompt": "Describe a scene",
      "params": { "length": "short" }
    }
    """
    try:
        orch = _get_orchestrator()
        if not hasattr(orch, "execute"):
            raise HTTPException(status_code=501, detail="AgentOrchestrator does not implement execute.")
        result = orch.execute(agent_type, payload)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed for '{agent_type}': {e}")
