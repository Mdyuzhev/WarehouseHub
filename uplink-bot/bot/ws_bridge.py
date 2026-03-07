"""
WebSocket bridge to Uplink botservice.
Connects as SDK bot, receives /wh commands, processes them, replies via WS.
"""

import asyncio
import json
import logging

import websockets

from config import UPLINK_WS_URL, UPLINK_BOT_TOKEN

logger = logging.getLogger(__name__)

RECONNECT_DELAYS = [1, 2, 5, 10, 30]

_command_handler = None


def set_command_handler(handler):
    """Register async handler: async def handler(command, args) -> str"""
    global _command_handler
    _command_handler = handler


async def _send_action(ws, action):
    """Send action and return action_id."""
    import time
    action_id = f"sdk_{int(time.time() * 1000)}"
    action["action_id"] = action_id
    await ws.send(json.dumps(action))
    return action_id


async def bridge_loop():
    """Main reconnect loop."""
    if not UPLINK_WS_URL or not UPLINK_BOT_TOKEN:
        logger.info("[ws_bridge] UPLINK_WS_URL or UPLINK_BOT_TOKEN not set, bridge disabled")
        return

    ws_url = UPLINK_WS_URL.rstrip("/")
    # Build WS URL: wss://host/bot-ws/<token>
    url = f"{ws_url}/bot-ws/{UPLINK_BOT_TOKEN}"
    attempt = 0

    while True:
        try:
            logger.info(f"[ws_bridge] Connecting to {ws_url}/bot-ws/...")
            async with websockets.connect(url, ping_interval=30, ping_timeout=10) as ws:
                attempt = 0
                logger.info("[ws_bridge] Connected to Uplink")

                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    if msg.get("type") == "connected":
                        bot_id = msg.get("bot_id", "?")
                        rooms = msg.get("rooms", [])
                        logger.info(f"[ws_bridge] Handshake OK, bot={bot_id}, rooms={len(rooms)}")
                        continue

                    if msg.get("type") == "ack":
                        continue

                    if msg.get("type") == "error":
                        logger.error(f"[ws_bridge] Error: {msg.get('error')}")
                        continue

                    if msg.get("type") == "event":
                        event = msg.get("event", {})
                        asyncio.create_task(_handle_event(ws, event))

        except (websockets.ConnectionClosed, ConnectionRefusedError, OSError) as e:
            logger.warning(f"[ws_bridge] Disconnected: {e}")
        except Exception as e:
            logger.error(f"[ws_bridge] Unexpected error: {e}", exc_info=True)

        delay = RECONNECT_DELAYS[min(attempt, len(RECONNECT_DELAYS) - 1)]
        attempt += 1
        logger.info(f"[ws_bridge] Reconnecting in {delay}s (attempt {attempt})")
        await asyncio.sleep(delay)


async def _handle_event(ws, event):
    """Process incoming event from Uplink."""
    if event.get("type") != "command":
        return

    command = event.get("command", "")
    args = event.get("args", [])
    room_id = event.get("room_id", "")

    logger.info(f"[ws_bridge] Command: {command} {args} from {event.get('sender')}")

    if not _command_handler:
        return

    try:
        result = await _command_handler(command, args)
        if result:
            # Send via webhook so all messages come from bot_wh_ci
            from bot import uplink
            await uplink.send_message(text=result)
    except Exception as e:
        logger.error(f"[ws_bridge] Handler error: {e}", exc_info=True)
        try:
            from bot import uplink
            await uplink.send_message(text=f"Error: {e}")
        except Exception:
            pass
