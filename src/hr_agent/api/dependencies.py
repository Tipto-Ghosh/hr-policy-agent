from __future__ import annotations

from typing import Annotated, Any
from functools import lru_cache
from typing import AsyncIterator
from fastapi import Depends, Request

from hr_agent.agent.graph import GraphDeps, compile_graph
from hr_agent.agent.runner import default_deps
from hr_agent.api.config import get_api_settings, APISettings
from hr_agent.core.settings import get_settings, Settings
from hr_agent.memory.store import get_store



def api_settings_dep() -> APISettings:
    return get_api_settings()

def settings_dep() -> Settings:
    return get_settings()


# agent deps
@lru_cache()
def _get_graph_deps() -> GraphDeps:
    return default_deps()

def graph_deps_dep() -> GraphDeps:
    return _get_graph_deps()

def graph_dep(request: Request):
    """
    The compiled async graph is set on app.state during lifespan startup.
    Never cached at module level — it holds an aiosqlite connection bound
    to the running event loop.
    """
    return request.app.state.graph

APISettingsDep = Depends(api_settings_dep)
SettingsDep = Depends(settings_dep)
GraphDepsDep = Depends(_get_graph_deps)
# GraphDep = Depends(graph_dep)
GraphDep = Annotated[Any, Depends(graph_dep)]