import requests
import json
import time


def read_sse_stream(response):
    """Manually read and parse an SSE stream from a requests response"""
    buffer = ""
    for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
        if chunk:
            buffer += chunk
            lines = buffer.split("\n")
            # Keep the last incomplete line in the buffer
            buffer = lines.pop()

            for line in lines:
                line = line.strip()
                if line.startswith("data:"):
                    data = line[5:].strip()
                    if data:  # Only yield non-empty data
                        yield data
                # You can also handle other SSE fields like 'event:' here


def test_sse_flow():
    """Test with manual SSE parsing to avoid library errors"""

    print("Step 1: Connect to SSE and get session...")
    sse_response = requests.get("http://localhost:8000/sse", stream=True)
    print(f"Control channel status: {sse_response.status_code}")

    session_id = None
    for line in sse_response.iter_lines():
        if line:
            decoded = line.decode("utf-8").strip()
            print(f"SSE: {decoded}")
            if decoded.startswith("data:"):
                endpoint = decoded[5:].strip()
                if "session_id=" in endpoint:
                    session_id = endpoint.split("session_id=")[1].split("&")[0]
                    print(f"Got session ID: {session_id}")
                    break

    if not session_id:
        print("No session ID")
        return

    time.sleep(2)

    print("\nStep 2: Send calculator request...")
    response = requests.post(
        f"http://localhost:8000/messages/?session_id={session_id}",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "calculator",
                "arguments": {"operation": "add", "a": 5, "b": 3},
            },
        },
        headers={"Content-Type": "application/json"},
    )
    print(f"POST status: {response.status_code}")

    print("\nStep 3: Connect to results channel WITH CORRECT HEADERS...")
    results_url = f"http://localhost:8000/messages/?session_id={session_id}"

    # Connect with the headers the server requires
    results_response = requests.get(
        results_url,
        stream=True,
        headers={
            "Accept": "text/event-stream",
            "Content-Type": "text/event-stream",  # Required by your server
        },
    )

    print(f"Results channel status: {results_response.status_code}")

    if results_response.status_code != 200:
        print(f"Failed to connect to results channel")
        # Print more debug info
        print(f"Response headers: {dict(results_response.headers)}")
        return

    print("✓ Connected to results channel")

    print("\nStep 4: Listening for result (timeout: 15 seconds)...")
    start_time = time.time()
    timeout = 15
    result_found = False

    # Use our manual SSE parser
    for data in read_sse_stream(results_response):
        if time.time() - start_time > timeout:
            print("Timeout waiting for result")
            break

        print(f"SSE data received: {data}")

        # Check if this is our result
        if "result" in data.lower() or "8" in data:
            print(f"\n✅✅✅ RESULT FOUND: {data}")
            result_found = True
            break

    if not result_found:
        print("No result received within timeout")

    # Always close the connection
    results_response.close()
    print("Test complete.")


if __name__ == "__main__":
    test_sse_flow()
