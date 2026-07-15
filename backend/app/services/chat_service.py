import uuid
import json
from pathlib import Path
from datetime import datetime

CHAT_FILE = Path("storage/chats.json")


class ChatService:

    def __init__(self):

        if CHAT_FILE.exists():

            with open(CHAT_FILE, "r") as f:
                self.chats = json.load(f)

        else:

            self.chats = []

    def save(self):

        with open(CHAT_FILE, "w") as f:

            json.dump(
                self.chats,
                f,
                indent=4,
            )

    def new_chat(self):

        chat = {
            "id": str(uuid.uuid4()),
            "title": "New Chat",
            "created_at": datetime.now().isoformat(),
            "messages": [],
        }

        self.chats.insert(0, chat)

        self.save()

        return chat

    def get_chat(self, chat_id):

        for chat in self.chats:
            if chat["id"] == chat_id:
                return chat

        return None

    def add_message(self, chat_id, role, content, sources=None):

        chat = self.get_chat(chat_id)

        if chat is None:
            return

        chat["messages"].append(
    {
        "role": role,
        "content": content.strip(),
        # Only assistant messages carry retrieval sources; user messages
        # simply get None here. Previously this field didn't exist at all,
        # so reopening a past chat always showed an empty "Retrieved
        # Chunks" section for every prior answer, even though the answer
        # itself was preserved.
        "sources": sources,
        "timestamp": datetime.now().isoformat(),
    }
)

        # Automatically use the first user question as the title
        if (
            role == "user"
            and chat["title"] == "New Chat"
        ):
            chat["title"] = content.strip()[:40]

        self.save()

    def get_all_chats(self):
        return self.chats


chat_service = ChatService()