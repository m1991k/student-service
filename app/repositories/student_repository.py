from bson import ObjectId
from app.db.mongodb import db
import logging

logger = logging.getLogger(__name__)

class StudentRepository:
    collection = db.students

    @staticmethod
    async def create(student: dict):
        logger.debug(f"Creating student with data: {student}")
        try:
            result = await StudentRepository.collection.insert_one(student)
            logger.debug(f"Student inserted with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error in create: {e}", exc_info=True)
            raise

    @staticmethod
    async def get_all():
        logger.debug("Fetching all students from MongoDB")
        try:
            docs = []
            async for d in StudentRepository.collection.find():
                logger.debug(f"Found document: {d}")
                d["id"] = str(d["_id"])
                d.pop("_id", None)
                docs.append(d)
            logger.debug(f"Retrieved {len(docs)} documents")
            return docs
        except Exception as e:
            logger.error(f"Error in get_all: {e}", exc_info=True)
            raise

    @staticmethod
    async def get_by_id(student_id: str):
        logger.debug(f"Fetching student by ID: {student_id}")
        try:
            d = await StudentRepository.collection.find_one({"_id": ObjectId(student_id)})
            if not d:
                logger.debug(f"Student not found: {student_id}")
                return None
            d["id"] = str(d["_id"])
            d.pop("_id", None)
            logger.debug(f"Retrieved student: {d}")
            return d
        except Exception as e:
            logger.error(f"Error in get_by_id: {e}", exc_info=True)
            raise

    @staticmethod
    async def update(student_id: str, payload: dict):
        logger.debug(f"Updating student {student_id} with payload: {payload}")
        try:
            result = await StudentRepository.collection.update_one({"_id": ObjectId(student_id)}, {"$set": payload})
            logger.debug(f"Update result: matched_count={result.matched_count}, modified_count={result.modified_count}")
            return result
        except Exception as e:
            logger.error(f"Error in update: {e}", exc_info=True)
            raise

    @staticmethod
    async def delete(student_id: str):
        logger.debug(f"Deleting student {student_id}")
        try:
            result = await StudentRepository.collection.delete_one({"_id": ObjectId(student_id)})
            logger.debug(f"Delete result: deleted_count={result.deleted_count}")
            return result
        except Exception as e:
            logger.error(f"Error in delete: {e}", exc_info=True)
            raise
