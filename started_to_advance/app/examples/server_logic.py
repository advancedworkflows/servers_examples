from typing import Any, Callable


routes: dict[str, Callable[[Any], Any]] = {}


def route(path: str):
    def register_route(func):
        routes[path] = func
        return func
    return register_route


@route("/some")
def get_some():
    return "Some <additional info>"


request: str = ""


while request != "quit":
    request = input(">    ")

    if request in routes:
        response = routes[request]()
        print(response, end="\n\n")
    else:
        print("not found")
