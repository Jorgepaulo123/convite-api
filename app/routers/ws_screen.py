from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws_manager import screen_hub

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/screen")
async def screen_websocket(websocket: WebSocket) -> None:
    await screen_hub.connect(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            if msg.strip().lower() == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        screen_hub.disconnect(websocket)
