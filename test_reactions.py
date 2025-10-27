#!/usr/bin/env python3
"""
Test script for the new WebSocket reaction handlers.
Tests the add_reaction and remove_reaction event types.
"""

import asyncio
import json
import websockets
import uuid

async def test_reaction_handlers():
    """Test the new add_reaction and remove_reaction event handlers"""
    
    # Connect to the WebSocket
    uri = "ws://localhost:8000/ws/test_room/test_user"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")
            
            # First, send a message to get a message ID
            message_id = str(uuid.uuid4())
            test_message = {
                "type": "message",
                "content": "Test message for reactions"
            }
            
            await websocket.send(json.dumps(test_message))
            print("Sent test message")
            
            # Receive the message broadcast to get the actual message ID
            response = await websocket.recv()
            message_data = json.loads(response)
            if message_data.get("type") == "message":
                actual_message_id = message_data.get("message_id")
                print(f"Received message with ID: {actual_message_id}")
                
                # Test add_reaction event
                add_reaction = {
                    "type": "add_reaction",
                    "message_id": actual_message_id,
                    "emoji": "👍"
                }
                
                await websocket.send(json.dumps(add_reaction))
                print("Sent add_reaction event")
                
                # Receive the reaction_update response
                response = await websocket.recv()
                reaction_data = json.loads(response)
                print(f"Add reaction response: {reaction_data}")
                
                # Verify required fields are present
                if reaction_data.get("type") == "reaction_update":
                    required_fields = ["message_id", "emoji", "users"]
                    missing_fields = [field for field in required_fields if field not in reaction_data]
                    if missing_fields:
                        print(f"❌ Missing fields in reaction_update: {missing_fields}")
                    else:
                        print(f"✅ All required fields present: message_id={reaction_data['message_id']}, emoji={reaction_data['emoji']}, users={reaction_data['users']}")
                
                # Test remove_reaction event
                remove_reaction = {
                    "type": "remove_reaction",
                    "message_id": actual_message_id,
                    "emoji": "👍"
                }
                
                await websocket.send(json.dumps(remove_reaction))
                print("Sent remove_reaction event")
                
                # Receive the reaction_update response
                response = await websocket.recv()
                reaction_data = json.loads(response)
                print(f"Remove reaction response: {reaction_data}")
                
                # Verify required fields are present
                if reaction_data.get("type") == "reaction_update":
                    required_fields = ["message_id", "emoji", "users"]
                    missing_fields = [field for field in required_fields if field not in reaction_data]
                    if missing_fields:
                        print(f"❌ Missing fields in reaction_update: {missing_fields}")
                    else:
                        print(f"✅ All required fields present: message_id={reaction_data['message_id']}, emoji={reaction_data['emoji']}, users={reaction_data['users']}")
                
                print("✅ Test completed successfully!")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    print("Starting reaction handler tests...")
    asyncio.run(test_reaction_handlers())
