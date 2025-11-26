"""Local WebSocket testing script.

This script demonstrates how to test the WebSocket feature locally.
Run this after starting the server.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import websockets
except ImportError:
    print("ERROR: websockets library not installed.")
    print("Install with: pip install websockets")
    sys.exit(1)


async def test_default_handler():
    """Test default WebSocket handler (echo behavior)."""
    print("\n" + "=" * 60)
    print("Test 1: Default Handler (Echo Behavior)")
    print("=" * 60)

    uri = "ws://localhost:8000/ws/products"

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to WebSocket")

            # Send test message
            test_message = "Hello, WebSocket!"
            await websocket.send(test_message)
            print(f"✓ Sent: {test_message}")

            # Receive echo response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"✓ Received: {data}")

            assert data["message"] == "Received"
            assert data["data"] == test_message
            print("✓ Default handler working correctly!")

    except Exception as e:
        print(f"✗ Error: {e}")
        return False

    return True


async def test_custom_handler():
    """Test custom WebSocket handler (if configured)."""
    print("\n" + "=" * 60)
    print("Test 2: Custom Handler (if configured)")
    print("=" * 60)

    uri = "ws://localhost:8000/ws/products"

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to WebSocket")

            # Receive connection message (if custom handler sends one)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(response)
                print(f"✓ Received connection message: {data}")
            except asyncio.TimeoutError:
                print("ℹ No connection message (using default handler)")

            # Send test message
            test_message = json.dumps({"action": "test", "data": "hello"})
            await websocket.send(test_message)
            print(f"✓ Sent: {test_message}")

            # Receive response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"✓ Received: {data}")

            print("✓ Custom handler test completed!")

    except Exception as e:
        print(f"✗ Error: {e}")
        return False

    return True


async def test_multiple_connections():
    """Test multiple concurrent connections."""
    print("\n" + "=" * 60)
    print("Test 3: Multiple Concurrent Connections")
    print("=" * 60)

    uri = "ws://localhost:8000/ws/products"

    try:
        async with websockets.connect(uri) as ws1, websockets.connect(uri) as ws2:
            print("✓ Connected two WebSocket clients")

            # Send messages from both connections
            await ws1.send("Message from client 1")
            await ws2.send("Message from client 2")
            print("✓ Sent messages from both clients")

            # Receive responses
            response1 = await ws1.recv()
            response2 = await ws2.recv()

            data1 = json.loads(response1)
            data2 = json.loads(response2)

            print(f"✓ Client 1 received: {data1}")
            print(f"✓ Client 2 received: {data2}")

            assert data1["data"] == "Message from client 1"
            assert data2["data"] == "Message from client 2"
            print("✓ Multiple connections working correctly!")

    except Exception as e:
        print(f"✗ Error: {e}")
        return False

    return True


async def main():
    """Run all WebSocket tests."""
    print("=" * 60)
    print("WebSocket Local Testing")
    print("=" * 60)
    print("\n⚠ Make sure the server is running on localhost:8000")
    print("   Start server with: python -m src.presentation.app")
    print("   Or use your app entry point")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        return

    results = []

    # Test 1: Default handler
    try:
        result = await test_default_handler()
        results.append(("Default Handler", result))
    except Exception as e:
        print(f"✗ Test 1 failed: {e}")
        results.append(("Default Handler", False))

    # Test 2: Custom handler
    try:
        result = await test_custom_handler()
        results.append(("Custom Handler", result))
    except Exception as e:
        print(f"✗ Test 2 failed: {e}")
        results.append(("Custom Handler", False))

    # Test 3: Multiple connections
    try:
        result = await test_multiple_connections()
        results.append(("Multiple Connections", result))
    except Exception as e:
        print(f"✗ Test 3 failed: {e}")
        results.append(("Multiple Connections", False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")


if __name__ == "__main__":
    asyncio.run(main())

