import asyncio
import vertexai
from vertexai import agent_engines

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

PROJECT_ID=os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION=os.getenv("GOOGLE_CLOUD_LOCATION")
RESOURCE_NAME = os.getenv("RESOURCE_NAME")

async def run():
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    print(PROJECT_ID)

    print(f"Connecting to Agent Engine: {RESOURCE_NAME}...")
    adk_app = agent_engines.get(RESOURCE_NAME)

    USER_ID = "Julia"

    print(f"Creating session for user: {USER_ID}...")
    session = await adk_app.async_create_session(user_id=USER_ID)
    print(f"Session created: {session['id']}")

    print("Streaming query...")
    async for event in adk_app.async_stream_query(
        user_id=USER_ID,
        session_id=session['id'],
        message="Escribe una Calculadora que solo haga sumas"
    ):
        print(event)

if __name__ == "__main__":
    asyncio.run(run())