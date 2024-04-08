from functools import wraps
from db.service_provider import ServiceProvider

global service_provider  # Not recommended for large applications
service_provider = ServiceProvider()

def get_service_provider():
  return service_provider

# Decorator to inject the service provider into a function
# allows to pass additional arguments to the function
def inject_service_provider(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        service_provider = get_service_provider()
        return await func(service_provider, *args, **kwargs)
    return wrapper