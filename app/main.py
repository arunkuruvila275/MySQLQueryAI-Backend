import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, text
import openai
import os
from .database import SessionLocal, engine, Base
from .models import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Ensure the API key is set
openai.api_key = os.getenv('OPENAI_API_KEY')

# Initialize database
Base.metadata.create_all(bind=engine)

# Set up CORS
origins = [
    "http://localhost:3000",  # React dev server
    # Add more origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionDetails(BaseModel):
    username: str
    password: str
    hostname: str
    database: str

class QueryRequest(BaseModel):
    natural_language_query: str
    connection_details: ConnectionDetails

# Global storage for table metadata
table_metadata = {}

def get_db_url(connection_details: ConnectionDetails):
    return f"mysql+pymysql://{connection_details.username}:{connection_details.password}@{connection_details.hostname}/{connection_details.database}"

def fetch_table_metadata(db: Session):
    metadata = {}
    tables = db.execute(text("SHOW TABLES")).fetchall()
    for (table_name,) in tables:
        create_table_query = db.execute(text(f"SHOW CREATE TABLE {table_name}")).fetchone()
        metadata[table_name] = create_table_query[1]  # Access the second element of the tuple
    return metadata


@app.post("/connect/")
async def connect(connection_details: ConnectionDetails):
    try:
        # Test the database connection
        db_url = get_db_url(connection_details)
        engine = create_engine(db_url)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        # Fetch table metadata
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        global table_metadata
        table_metadata = fetch_table_metadata(db)

        # Send metadata to OpenAI to inform the model about the database structure
        # openai.api_key = os.getenv('OPENAI_API_KEY')
        # for table_name, create_table_query in metadata.items():
        #    openai.completions.create(
        #        model="gpt-3.5-turbo-instruct",
        #        prompt=f"Here is the structure of the table {table_name}:\n\n{create_table_query}",
        #        max_tokens=150,
        #        temperature=0
        #    )

        return {"message": "Connection successful"}
    except Exception as e:
        logger.error(f"Connection failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")


@app.get("/")
async def read_root():
    return {"message": "Welcome to MySQLQueryAI"}


@app.post("/translate_query/")
async def translate_query(request: QueryRequest):
    logger.info("Received translate_query request")

    # Create the database connection
    db_url = get_db_url(request.connection_details)
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # Include table metadata in the prompt
    metadata_prompt = ""
    for table_name, create_table_query in table_metadata.items():
        metadata_prompt += f"Table {table_name} structure:\n{create_table_query}\n\n"

    # Craft a prompt that instructs the model to return only the SQL query
    prompt = f"{metadata_prompt}Convert the following natural language query to a SQL query. Only return the SQL query, no other text:\n\n{request.natural_language_query}" 
    
    logger.info("Sending prompt to OpenAI")
    logger.debug(f"Prompt: {prompt}")

    response = openai.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=150,
        temperature=0   # Setting temperature to 0 for more deterministic responses
    )
    sql_query = response.choices[0].text.strip()

    # Extract the last line of the SQL query
    sql_query_last_line = sql_query.split('\n')[-1].strip()

    # Debugging: Print the generated SQL query
    logger.info(f"Generated SQL Query: {sql_query_last_line}")

    try:
        result = db.execute(text(sql_query_last_line)).fetchall()
        # Convert result to a list of dictionaries
        result_dict = [dict(row._mapping) for row in result]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query execution failed: {str(e)}")

    return {"sql_query": sql_query_last_line, "result": result_dict}
