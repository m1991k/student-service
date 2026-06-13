from bson import ObjectId
from app.db.mongodb import db

class StudentRepository:
    collection = db.students

    @staticmethod
    async def create(student: dict):
        result = await StudentRepository.collection.insert_one(student)
        return str(result.inserted_id)

    @staticmethod
    async def get_all():
        docs = []
        async for d in StudentRepository.collection.find():
            d["id"] = str(d["_id"])
            d.pop("_id", None)
            docs.append(d)
        return docs

    @staticmethod
    async def get_by_id(student_id:str):
        d = await StudentRepository.collection.find_one({"_id": ObjectId(student_id)})
        if not d:
            return None
        d["id"]=str(d["_id"])
        d.pop("_id",None)
        return d

    @staticmethod
    async def update(student_id:str, payload:dict):
        return await StudentRepository.collection.update_one({"_id": ObjectId(student_id)}, {"$set": payload})

    @staticmethod
    async def delete(student_id:str):
        return await StudentRepository.collection.delete_one({"_id": ObjectId(student_id)})
