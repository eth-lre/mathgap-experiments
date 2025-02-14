from typing import Any, Dict, Type

class Renderer:
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.render(*args, **kwds)

    def render(self, *args: Any, **kwds: Any) -> Any:
        ...

class PerTypeRenderer(Renderer):
    """ 
        Renderer that selects the appropriate renderer depending on the type of the object that should be rendered
        Will pick the first renderer that can render any of the baseclasses of said object,
        so make sure you register them by class-hierarchy!
    """
    def __init__(self, renderers: Dict[Type, Renderer], default_renderer: Renderer) -> None:
        self.renderers = renderers
        self.default_renderer = default_renderer

    def render(self, obj: Any, *args: Any, **kwds: Any) -> Any:
        for cls,renderer in self.renderers.items():
            if isinstance(obj, cls):
                return renderer.render(obj, *args, **kwds)
        return self.default_renderer.render(obj, *args, **kwds)