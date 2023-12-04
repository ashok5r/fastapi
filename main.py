from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi import File, UploadFile
from databases import Database
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table
from sqlalchemy.sql import select

app = FastAPI()

# Connect to SQLite database
DATABASE_URL = "sqlite:///./db/users.db"
database = Database(DATABASE_URL)

# Define SQLAlchemy Model
metadata = MetaData()
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String),
    Column("age", Integer),
)

# Mount static files (for CSS, JS, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 templates configuration
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
async def startup_db():
    await database.connect()


@app.on_event("shutdown")
async def shutdown_db():
    await database.disconnect()


@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...), name_col: int = Form(...), age_col: int = Form(...)):
    contents = await file.read()
    contents = contents.decode("utf-8").split("\n")

    # Assuming CSV structure is simple and the first line contains column headers
    headers = contents[0].split(",")

    # Get selected column indices
    name_index = name_col - 1
    age_index = age_col - 1

    # Process CSV data and save to database
    async with database.transaction():
        for line in contents[1:]:
            data = line.split(",")
            if len(data) >= max(name_index, age_index):
                name = data[name_index]
                age = data[age_index]
                query = users.insert().values(name=name, age=age)
                await database.execute(query)

    return {"filename": file.filename}
