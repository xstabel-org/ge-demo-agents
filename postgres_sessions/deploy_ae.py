import os
from dotenv import load_dotenv

from agent import root_agent

import vertexai 
from vertexai import agent_engines

from google.adk.sessions import DatabaseSessionService

load_dotenv(override=True)

MODEL=os.getenv("GEMINI_MODEL")
PROJECT_ID=os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION=os.getenv("GOOGLE_CLOUD_LOCATION")
STAGING_BUCKET = os.getenv("STAGING_BUCKET")

db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASS")
db_name = os.getenv("DB_NAME")
postgres_instance_uri = os.getenv("POSTGRES_INSTANCE_URI")

vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET) 

app = agent_engines.AdkApp(
    agent=root_agent,
    session_service_builder=lambda: DatabaseSessionService(
        db_url=f"postgresql://{db_user}:{db_pass}@{postgres_instance_uri}/{db_name}",
        echo=True,
    ),
    enable_tracing=True,
) 

remote_agent = agent_engines.create(
    app,
    display_name="Code Writer Agent - Sessions in Postgres ",
    requirements=["google-cloud-aiplatform[adk, agent_engines]==1.126.1", "google-adk==1.18.0", "psycopg2-binary"],
    env_vars = {
                "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
                "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true",
                }
)
