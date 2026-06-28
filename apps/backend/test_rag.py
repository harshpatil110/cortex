import asyncio

from dotenv import load_dotenv

from services.rag_service import RagService

load_dotenv(".env")


async def test():
    rag = RagService()
    async for c in rag.stream_chat(
        "9bd940e8-609d-4a09-893c-82f94a46845e",
        [],
        "tell me about agentic ai from my reels",
    ):
        print(c)


asyncio.run(test())
