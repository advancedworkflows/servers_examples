from typing import Annotated


def say_hello(name: Annotated[str, "this is just metadata"]) -> str:
    return f"Hello {name}"

def get_something_or_nothing(something: str | None = None):
    if something is not None:
        return something.title()
    else:
        return "Stranger"
    
def get_full_name(first_name: str, second_name: str, age: int):
    full_name = get_something_or_nothing(first_name)+" "+second_name.title()+"_"+str(age)
    return full_name

if __name__ == "__main__":
    name = get_full_name("jon", "doe", 2)
    print(name)