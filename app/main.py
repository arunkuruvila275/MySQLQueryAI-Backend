from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, text
import openai
import os
from .database import SessionLocal, engine, Base
from .models import Base

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/connect/")
async def connect(connection_details: ConnectionDetails):
    try:
        # Test the database connection
        db_url = f"mysql+pymysql://{connection_details.username}:{connection_details.password}@{connection_details.hostname}/{connection_details.database}"
        engine = create_engine(db_url)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"message": "Connection successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")

@app.get("/")
async def read_root():
    return {"message": "Welcome to MySQLQueryAI"}

@app.post("/translate_query/")
async def translate_query(request: QueryRequest, db: Session = Depends(get_db)):
   
   # Craft a prompt that instructs the model to return only the SQL query
    prompt = f"Convert the following natural language query to a SQL query, and return only the SQL query:\n\n{request.natural_language_query}"
    
    response = openai.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=150,
        temperature=0   # Setting temperature to 0 for more deterministic responses
    )
    sql_query = response.choices[0].text.strip()

    # Debugging: Print the generated SQL query
    print("Generated SQL Query:", sql_query)

    try:
        result = db.execute(text(sql_query)).fetchall()
        # Convert result to a list of dictionaries
        result_dict = [dict(row._mapping) for row in result]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query execution failed: {str(e)}")

    return {"sql_query": sql_query, "result": result_dict}
