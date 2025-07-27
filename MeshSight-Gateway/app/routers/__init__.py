from .v1.AnalysisRouter import router as v1_analysis_router
from .v1.AppRouter import router as v1_app_router
from .v1.MapRouter import router as v1_map_router
from .v1.NodeRouter import router as v1_node_router


routers = [
    v1_analysis_router,
    v1_app_router,
    v1_map_router,
    v1_node_router,
]
