# How to deploy an Agent into Agent Engine with the Database Session Service in Postgres:

1. Create a Postgres Cloud SQL instance and an empty database within it
2. To run locally:
Install cloud-sql-proxy: https://docs.cloud.google.com/sql/docs/mysql/connect-instance-auth-proxy#install-proxy

In one terminal Start the Cloud SQL Auth Proxy:
```bash
./cloud-sql-proxy <PROJECT_ID>:<DB_REGION>:<INSTANCE_ID> --port=5432
```

In another terminal:
```bash
adk web --session_service_uri="postgresql://<DB_USER>:<DB_PASSWORD>@127.0.0.1:5432/<DB_NAME>"
```

3. To deploy to Agent Engine:

    3.0 Fill in the .env variables. POSTGRES_INSTANCE_URI is the Public IP under "Conncetions" followed by the port :5432
    
    3.1 Add your local IP to the Authorized Networks of the Postgres Instance (under "Connections/Networking/Public IP") so the tables can be created in the DB during the deployment.

    3.3 Add all external IPs 0.0.0.0/0 under "Connections/Networking/Public IP" to enable deployment for testing. You must then pivot to a more secure connection method (like a VPC Peering setup for Cloud SQL and your Agent Engine VPC, or using the Cloud SQL Auth Proxy if your deployment supports it) for long-term production use.*
    
    3.2 Run deploy_ae.py

4. Give the Agent Engine Servicce Account permissions on the PostgresSQL Instace (under "Users").

5. Run query_ae.py to test the deployment.



*See this bug to configure Private Service Connect interface: https://b.corp.google.com/issues/455637819
