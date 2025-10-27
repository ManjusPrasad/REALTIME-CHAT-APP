#!/usr/bin/env python3
"""
Demo script to show the reaction_update broadcasting functionality.
This demonstrates how reaction updates are broadcast to all clients in real-time.
"""

import asyncio
import json
import websockets
import uuid

async def create_client(name: str, room: str = "demo_room"):
    """Create a client that connects and listens for messages"""
    uri = f"ws://localhost:8000/ws/{room}/{name}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"[{name}] Connected to room: {room}")
            
            # If this is the first client, send a message and react to it
            if name == "client1":
                await asyncio.sleep(1)  # Wait for other clients to connect
                
                # Send a message
                test_message = {
                    "type": "message",
                    "content": "Hello! React to this message 👋"
                }
                await websocket.send(json.dumps(test_message))
                print(f"[{name}] Sent test message")
                
                # Wait for the message to be broadcast back
                response = await websocket.recv()
                message_data = json.loads(response)
                
                if message_data.get("type") == "message":
                    message_id = message_data.get("message_id")
                    print(f"[{name}] Message ID: {message_id}")
                    
                    await asyncio.sleep(0.5)
                    
                    # Add a reaction
                    add_reaction = {
                        "type": "add_reaction",
                        "message_id": message_id,
                        "emoji": "❤️"
                    }
                    await websocket.send(json.dumps(add_reaction))
                    print(f"[{name}] Added ❤️ reaction")
                    
                    await asyncio.sleep(2)
                    
                    # Add another reaction
                    add_reaction2 = {
                        "type": "add_reaction", 
                        "message_id": message_id,
                        "emoji": "🚀"
                    }
                    await websocket.send(json.dumps(add_reaction2))
                    print(f"[{name}] Added 🚀 reaction")
                    
                    await asyncio.sleep(2)
                    
                    # Remove the first reaction
                    remove_reaction = {
                        "type": "remove_reaction",
                        "message_id": message_id,
                        "emoji": "❤️"
                    }
                    await websocket.send(json.dumps(remove_reaction))
                    print(f"[{name}] Removed ❤️ reaction")
            
            # Listen for all incoming messages
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(response)
                    
                    if data.get("type") == "reaction_update":
                        print(f"[{name}] 🔄 REACTION UPDATE: message_id={data.get('message_id')}, emoji={data.get('emoji')}, users={data.get('users')}")
                    elif data.get("type") == "message":
                        print(f"[{name}] 💬 MESSAGE: {data.get('content')}")
                    elif data.get("type") in ["join", "leave"]:
                        print(f"[{name}] 🔔 {data.get('type').upper()}: {data.get('user')}")
                    
                except asyncio.TimeoutError:
                    print(f"[{name}] Timeout, disconnecting...")
                    break
                    
    except Exception as e:
        print(f"[{name}] Error: {e}")

async def run_demo():
    """Run the demo with multiple clients"""
    print("🚀 Starting reaction broadcasting demo...")
    print("This will create 3 clients and demonstrate real-time reaction updates")
    print("-" * 60)
    
    # Create multiple clients concurrently
    tasks = [
        create_client("client1"),
        create_client("client2"), 
        create_client("client3")
    ]
    
    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    print("📡 Reaction Update Broadcasting Demo")
    print("Make sure the server is running on localhost:8000")
    print("=" * 60)
    
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
