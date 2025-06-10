# Generated with help from ChatGPT (1-74, 132-158)

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from pathlib import Path
from PIL import Image
import json
import bcrypt


app = FastAPI()
# Allow frontend requests (CORS policy)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sangjungpark.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str
    pass_sha256: str

@app.post("/login")
def login(data: LoginRequest):
    id_file = Path("data") / "id.json"
    ids = json.loads(id_file.read_text())

    # Find the user entry
    entry = next((entry for entry in ids if entry.get("username") == data.username), None)

    if not entry:
        return {"message": "User not found"}

    # Check password hash
    if bcrypt.checkpw(data.pass_sha256.encode(), entry["pass_hash"].encode("utf-8")):
        return {"message": "Login successful", "success": True}
    else:
        return {"message": "Invalid password"}


class Answer(BaseModel):
    question: str
    question_index: int
    answer: int

class QuizSubmission(BaseModel):
    date: str
    responses: List[Answer]
    username: str
    pass_sha256: str
    

@app.post("/submit-quiz")
def submit_quiz(data: QuizSubmission):
    data_to_save = {
        "date": data.date,
        "responses": [resp.dict() for resp in data.responses],
        "username": data.username,
    }

    user_dir = Path("data") / data_to_save['username']
    print(user_dir)
    quiz_file = user_dir / f"{data_to_save['date']}.json"
    quiz_file.write_text(json.dumps(data_to_save, indent=4), encoding="utf-8")

    cat_file = user_dir / f"{data_to_save['date']}.png"
    create_composite_image([response.answer + 1 for response in data.responses], cat_file)

    return {"message":f"result saved to {data_to_save['date']}.json"}

@app.post("/new-user")
def create_user_submit_quiz(data: QuizSubmission):
    data_to_save = {
        "date": data.date,
        "responses": [resp.dict() for resp in data.responses],
        "username": data.username,
    }

    user_check = save_user(data.username, bcrypt.hashpw(data.pass_sha256.encode(), bcrypt.gensalt()).decode("utf-8"))
    if user_check:
        raise HTTPException(status_code=400, detail="Username이 이미 사용중입니다. 다른 Username을 입력해주세요.")
    else:
        user_dir = Path("data") / data_to_save['username']
        user_dir.mkdir()

        quiz_file = user_dir / f"{data_to_save['date']}.json"
        quiz_file.write_text(json.dumps(data_to_save, indent=4), encoding="utf-8")

        cat_file = user_dir / f"{data_to_save['date']}.png"
        create_composite_image([response.answer + 1 for response in data.responses], cat_file)
        return {"message":f"result saved to {data_to_save['date']}.json"}

class CheckUser(BaseModel):
    username: str

@app.post("/get-user-images/")
def get_images(data: CheckUser):
    username = data.username
    png_files = list((Path('data') / username).glob('*.png'))
    png_dict = {png.name[:-4]: str(png) for png in png_files}
    return png_dict
    

def save_user(username: str, pass_hash: str):
    id_file = Path("data") / "id.json"

    if id_file.exists():
        ids = json.loads(id_file.read_text())
    else:
        ids = []

    new_user = {
        "username": username,
        "pass_hash": pass_hash,
    }

    if not any(entry.get("username") == username for entry in ids):
        ids.append(new_user)
        id_file.write_text(json.dumps(ids, indent=4))
        print(f"Added new user: {username}")
        return 0
    else:
        print(f"User '{username}' already exists.")
        return 1

    
def create_composite_image(indices, output_path='output.png'):
    """
    Creates a composite image by overlapping images from four directories.
    
    Args:
        indices (list): A list of four integers, each between 0 and 2.
        output_path (str): Path to save the final composite image.
    """
    # Define the image layer directories
    folders = ['img/base', 'img/texture', 'img/eyes', 'img/face']
    
    # Load the images in the specified order
    images = []
    for folder, idx in zip(folders, indices):
        img_path = f'{folder}/{idx}.png'
        img = Image.open(img_path).convert("RGBA")
        images.append(img)
    
    # Start with the base image
    composite = images[0].copy()

    # Overlay the remaining images
    for img in images[1:]:
        composite.alpha_composite(img)

    # Save the final image
    composite.save(output_path)
