import inspect


class Directive:
    header = "header"
    return_ = "return"
    ignore = "ignore"
    import_ = "import"
    empty = "empty"
    default = "default"


ALL_DIRECTIVES = {x[1]
                  for x in inspect.getmembers(Directive) if isinstance(x[1], str) and not x[0].startswith('_')}
