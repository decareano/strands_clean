# mcp_server.py
import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from typing import Dict
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

# Store active sessions
sessions: Dict[str, asyncio.Queue] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("MCP Server starting on http://localhost:8000")
    yield
    # Cleanup on shutdown
    sessions.clear()


app = FastAPI(lifespan=lifespan)


# Channel 1: Initial SSE connection for session setup
@app.get("/sse")
async def sse_endpoint(request: Request):
    """Initial SSE endpoint that provides a private message channel"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = asyncio.Queue()

    async def event_generator():
        # Send the private channel URL to the client
        yield {"event": "endpoint", "data": f"/messages/?session_id={session_id}"}

    return EventSourceResponse(event_generator())


# Channel 2: Private message channel for this session
@app.get("/messages/")
async def messages_endpoint(request: Request, session_id: str):
    """Private SSE channel for a specific session"""
    if session_id not in sessions:
        return {"error": "Invalid session"}, 404

    async def event_generator():
        queue = sessions[session_id]
        try:
            while True:
                # Wait for messages to send to this client
                message = await queue.get()
                if message == "TERMINATE":
                    break
                yield {"data": json.dumps(message)}
        except asyncio.CancelledError:
            print(f"Client disconnected from session {session_id}")
        finally:
            # Cleanup
            if session_id in sessions:
                del sessions[session_id]

    return EventSourceResponse(event_generator())


# Endpoint to receive calculation requests
@app.post("/messages/")
async def post_message(request: Request, session_id: str):
    """Receive calculation requests and send results via SSE"""
    if session_id not in sessions:
        return {"error": "Invalid session"}, 404

    try:
        data = await request.json()
        print(f"Received request for session {session_id}: {data}")

        # Parse the calculator request (following your JSON-RPC structure)
        if data.get("method") == "tools/call":
            params = data.get("params", {})
            if params.get("name") == "calculator":
                args = params.get("arguments", {})
                operation = args.get("operation", "add")
                a = args.get("a", 0)
                b = args.get("b", 0)

                # Perform calculation
                if operation == "add":
                    result = a + b
                elif operation == "subtract":
                    result = a - b
                elif operation == "multiply":
                    result = a * b
                elif operation == "divide":
                    result = a / b if b != 0 else "Error: Division by zero"
                else:
                    result = "Error: Unknown operation"

                # Prepare the result message
                result_message = {
                    "jsonrpc": "2.0",
                    "id": data.get("id", 1),
                    "result": {
                        "name": "calculator",
                        "content": {
                            "result": result,
                            "operation": (
                                f"{a} + {b}"
                                if operation == "add"
                                else f"{a} {operation} {b}"
                            ),
                            "a": a,
                            "b": b,
                        },
                    },
                }

                # Send result to client via SSE
                await sessions[session_id].put(result_message)
                print(f"Sent result to session {session_id}: {result}")

                return {"status": "accepted", "result_queued": True}

        # If not a calculator request
        await sessions[session_id].put({"error": "Unknown method"})
        return {"status": "accepted", "message": "Request queued"}

    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}, 400
    except Exception as e:
        print(f"Error processing request: {e}")
        return {"error": str(e)}, 500


# Root endpoint for testing
@app.get("/")
async def root():
    return {
        "message": "MCP Server with Calculator",
        "endpoints": {
            "sse": "GET /sse - Get SSE session",
            "messages": "GET /messages/?session_id={id} - Private message channel",
            "post": "POST /messages/?session_id={id} - Send calculation request",
        },
        "example": {
            "calculator_request": {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "calculator",
                    "arguments": {"operation": "add", "a": 5, "b": 3},
                },
            }
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
