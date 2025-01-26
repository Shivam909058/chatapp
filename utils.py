from fastapi import FastAPI
from typing import Callable
import asyncio
from datetime import datetime, timedelta

def repeat_every(*, seconds: float = 0, minutes: float = 0, hours: float = 0):
    def decorator(func: Callable):
        is_coroutine = asyncio.iscoroutinefunction(func)
        
        async def periodic():
            while True:
                try:
                    if is_coroutine:
                        await func()
                    else:
                        func()
                except Exception as e:
                    print(f"Error in periodic task {func.__name__}: {str(e)}")
                
                await asyncio.sleep(seconds + minutes * 60 + hours * 3600)
        
        def wrapper(app: FastAPI):
            @app.on_event("startup")
            async def start_periodic():
                asyncio.create_task(periodic())
            
            return app
        
        return wrapper
    
    return decorator 