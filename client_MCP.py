# test_client.py
import requests
import json
import time


def test_calculator():
    print("=" * 60)
    print("Testing MCP Calculator Server")
    print("=" * 60)

    # Step 1: Get SSE session
    print("\n1. Connecting to /sse...")
    sse_response = requests.get("http://localhost:8000/sse", stream=True)
    print(f"   Status: {sse_response.status_code}")

    session_id = None
    for line in sse_response.iter_lines():
        if line:
            decoded = line.decode("utf-8").strip()
            print(f"   SSE: {decoded}")
            if decoded.startswith("data:"):
                endpoint = decoded[5:].strip()
                session_id = endpoint.split("session_id=")[1].split("&")[0]
                print(f"   ✓ Session ID: {session_id}")
                break

    if not session_id:
        print("   ✗ No session received")
        return

    # Step 2: Connect to private message channel
    print(f"\n2. Connecting to private channel for session {session_id}...")
    messages_url = f"http://localhost:8000/messages/?session_id={session_id}"

    # Start listening for results in background
    import threading

    result = {"value": None}

    def listen_for_results():
        resp = requests.get(messages_url, stream=True)
        for line in resp.iter_lines():
            if line:
                decoded = line.decode("utf-8").strip()
                if decoded.startswith("data:"):
                    data = json.loads(decoded[5:].strip())
                    print(f"\n   📨 RESULT RECEIVED: {data}")
                    if "result" in data:
                        result["value"] = data

    listener = threading.Thread(target=listen_for_results, daemon=True)
    listener.start()
    time.sleep(1)  # Give listener time to connect

    # Step 3: Send calculation request
    print("\n3. Sending calculation: 5 + 3")
    calc_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "calculator",
            "arguments": {"operation": "add", "a": 5, "b": 3},
        },
    }

    response = requests.post(
        messages_url, json=calc_request, headers={"Content-Type": "application/json"}
    )

    print(f"   POST Status: {response.status_code}")
    print(f"   POST Response: {response.json()}")

    # Step 4: Wait for result
    print("\n4. Waiting for calculation result...")
    timeout = 10
    start_time = time.time()

    while time.time() - start_time < timeout:
        if result["value"] is not None:
            calc_result = result["value"]["result"]["content"]["result"]
            print(f"\n   ✅ CALCULATION RESULT: 5 + 3 = {calc_result}")
            print("   ✓ Test PASSED!")
            return
        time.sleep(0.5)

    print("   ⏰ Timeout waiting for result")
    print("   ✗ Test FAILED")


if __name__ == "__main__":
    test_calculator()
