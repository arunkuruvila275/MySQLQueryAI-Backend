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

# Configure logging1
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
    prompt = f"{metadata_prompt} Using the above metadata of all available tables, convert the following natural language query to a SQL query. Always make sure to use the correct table names and the feild names. Only return the SQL query, no other text:\n\n{request.natural_language_query}" 
    
    logger.info("Sending prompt to OpenAI")

    response = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a MySQL database admin expert, skilled in writing complex performance efficent queries using all the avaliable table metadata."},
            {"role": "user", "content": prompt}
        ]
        )
    sql_query = response.choices[0].message.content.strip()
    sql_query = sql_query.replace('```sql', '').replace('```', '').strip()

    logger.info(f"Generated SQL Query Full: {sql_query}")

    # Extract the last line of the SQL query
    #sql_query_last_line = sql_query.split('\n')[-1].strip()

    # Debugging: Print the generated SQL query
    logger.info(f"Generated SQL Query: {sql_query}")

    try:
        result = db.execute(text(sql_query)).fetchall()
        # Convert result to a list of dictionaries
        result_dict = [dict(row._mapping) for row in result]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query execution failed: {str(e)}")

    return {"sql_query": sql_query, "result": result_dict}
