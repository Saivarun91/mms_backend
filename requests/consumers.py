from channels.generic.websocket import AsyncWebsocketConsumer
import json


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.request_id = self.scope['url_route']['kwargs']['request_id']
        self.group_name = f"chat_{self.request_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        try:
            await self.send(text_data=json.dumps({"type": "system", "message": "connected"}))
        except Exception:
            pass

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            if text_data:
                data = json.loads(text_data)
                if data.get("type") == "ping":
                    await self.send(json.dumps({"type": "pong"}))
        except Exception:
            pass

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat",
            "message": event.get("message"),
        }))




