"""

Figma: https://www.figma.com/design/ZUa6tG2oArS2NfHlKpeBRn/Backend-Task?node-id=0-1&t=gEpbFOPR3Re3lclM-0

Objective:
Develop a unified API using FastAPI that can handle user management for three different projects.
The API should support operations such as creating users, retrieving user details, updating user
information, and deleting users. The data should be stored in a GCP database.

"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List
import firebase_admin
from firebase_admin import credentials, firestore
import my_logger
import my_utility

# Firestore Init
cred = credentials.Certificate("aviato-demo-firebase-service-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = FastAPI()


"""
Approach for dynamic user management based on projects:
 - When sending then data to the backend, send the project id associated
 - Based on the project id, the data will be populated in the database
 - If table/document does not exist already, it will be created based on the JSON key names
    - The type of the fields will be infered by checking the datatype

Limitation:
 - It is assumed that the JSON data sent to the server is perfectly structured so that
   proper tables/documents can be constructed and data can be inserted properly
"""

# Generic User Request Model
class UserRequest(BaseModel):
    project_id: int
    data: Dict[str, Any]


"""
Create User
    Endpoint: POST /add_users
    Request Body: JSON containing user details (e.g., username, email, project_id)
    Response: JSON with user details and a unique user ID
"""
@app.post('/add_user', response_model=dict)
async def add_user(req: UserRequest):
    try:
        project_id = str(req.project_id)
        user_data = my_utility.process_user_data(req.data)
        user_ref = db.collection(project_id).document()
        user_data["id"] = user_ref.id
        user_ref.set(user_data)
        my_logger.logger.info(f"User created with ID: {user_ref.id} in project: {project_id}")
        return user_data
    except Exception as e:
        my_logger.logger.error(f"Error creating user in project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


"""
GetUserDetails:
    Endpoint: GET /get_users
    Response: JSON with user details
"""
@app.get('/get_users/{project_id}', response_model=List[dict])
async def get_users(project_id: int):
    try:
        project_id = str(project_id)
        users_ref = db.collection(project_id)
        docs = users_ref.stream()
        users = [doc.to_dict() for doc in docs]
        my_logger.logger.info(f"Retrieved users for project: {project_id}")
        return users
    except Exception as e:
        my_logger.logger.error(f"Error retrieving users for project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


"""
UpdateUser Details:
    Endpoint: PATCH /update_users
    Request Body: JSON with updated user details
    Response: JSON with updated user details
"""
@app.patch('/update_users/{user_id}', response_model=dict)
async def update_users(user_id: str, req: UserRequest):
    try:
        project_id = str(req.project_id)
        user_data = my_utility.process_user_data(req.data)
        user_ref = db.collection(project_id).document(user_id)
        user = user_ref.get()
        if not user.exists:
            raise HTTPException(status_code=404, detail="User not found")
        existing_data = user.to_dict()
        existing_data.update(user_data)
        user_ref.set(existing_data)
        my_logger.logger.info(f"Updated user with ID: {user_id} in project: {project_id}")
        return existing_data
    except HTTPException as e:
        my_logger.logger.warning(f"User not found: {user_id} in project: {project_id}")
        raise e
    except Exception as e:
        my_logger.logger.error(f"Error updating user {user_id} in project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


"""
Delete User:
    Endpoint: DELETE /delete_users
    Response: JSON confirming deletion
"""
@app.delete('/delete_users/{project_id}/{user_id}', response_model=dict)
async def delete_users(project_id: int, user_id: str):
    try:
        project_id = str(project_id)
        user_ref = db.collection(project_id).document(user_id)
        user = user_ref.get()
        if not user.exists:
            raise HTTPException(status_code=404, detail="User not found")
        user_ref.delete()
        my_logger.logger.info(f"Deleted user with ID: {user_id} from project: {project_id}")
        return {"message": "User deleted successfully"}
    except HTTPException as e:
        my_logger.logger.warning(f"User not found: {user_id} in project: {project_id}")
        raise e
    except Exception as e:
        my_logger.logger.error(f"Error deleting user {user_id} in project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# Email List
class InviteRequest(BaseModel):
    recipients: List[str]

"""
Send Email Invite:
    Endpoint: POST /invite
    Response: JSON confirming invitation
"""
@app.post('/invite')
async def invite(req: InviteRequest):
    try:
        my_utility.send_invitation_email(req.recipients)
        return {"message": "Invitation emails sent successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        my_logger.logger.error(f"Error sending invitation emails: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
