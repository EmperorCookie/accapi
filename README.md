# ACCAPI
Assetto Corsa Competizione UDP broadcast API wrapper

# Usage
```py
import time

from accapi.client import AccClient, Event

# Modify appropriately
ACC_URL = "URL"
ACC_PORT = 9001
ACC_PASSWORD = "PASSWORD"

# Create client
client = AccClient()

# Register callback
def on_connection_state_change(event: Event) -> None:
    print(f"New connection state: {event.content}")

client.onConnectionStateChange.subscribe(on_connection_state_change)

# Explore callback content
def print_content_class(event: Event) -> None:
    print(f"Received event containing '{event.content.__class__.__name__}'")

client.onTrackDataUpdate.subscribe(print_content_class)
client.onEntryListCarUpdate.subscribe(print_content_class)
client.onRealtimeUpdate.subscribe(print_content_class)
client.onRealtimeCarUpdate.subscribe(print_content_class)
client.onBroadcastingEvent.subscribe(print_content_class)

# Only start the client after registering the callbacks
client.start(ACC_URL, ACC_PORT, ACC_PASSWORD)

# Control ACC
client.request_focus_change(carIndex=0, cameraSet="Bonnet") # Car focus and camera
client.request_hud_page(pageName="Help")
client.request_instant_replay(startTime=42, durationMs=10000)
time.sleep(10) # Wait for replay to finish

# Disconnect
client.stop()
```

# To Do
1. Improve documentation via docstrings for each method
1. Add unit tests
1. Publish as `pip` package
