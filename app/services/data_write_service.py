from typing import Dict, Any, Union
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.results import InsertOneResult, InsertManyResult, UpdateResult, DeleteResult


class DataWriteService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def write(self, request: Dict[str, Any]) -> Dict[str, Any]:
        collection_name = request.get("collection")
        operation = request.get("operation")
        data = request.get("data")
        filter_doc = request.get("filter")
        options = request.get("options", {})

        if not collection_name or not operation:
            raise ValueError("'collection' and 'operation' are required fields.")

        collection = self.db[collection_name]
        result: Union[InsertOneResult, InsertManyResult, UpdateResult, DeleteResult]

        if operation == "insert_one":
            if not isinstance(data, dict):
                raise ValueError("For 'insert_one', 'data' must be a single document (dict).")
            result = await collection.insert_one(data, **options)
            return {"status": "success", "inserted_id": str(result.inserted_id)}

        elif operation == "insert_many":
            if not isinstance(data, list):
                raise ValueError("For 'insert_many', 'data' must be a list of documents.")
            result = await collection.insert_many(data, **options)
            return {"status": "success", "inserted_ids": [str(id) for id in result.inserted_ids]}

        elif operation in ["update_one", "update_many"]:
            if not filter_doc:
                raise ValueError(f"'filter' is required for '{operation}' operation.")
            if not data:
                raise ValueError(f"'data' (update document) is required for '{operation}' operation.")

            if operation == "update_one":
                result = await collection.update_one(filter_doc, data, **options)
            else:
                # update_many
                result = await collection.update_many(filter_doc, data, **options)

            return {
                "status": "success",
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "upserted_id": str(result.upserted_id) if result.upserted_id else None
            }

        elif operation in ["delete_one", "delete_many"]:
            if not filter_doc:
                raise ValueError(f"'filter' is required for '{operation}' operation.")

            if operation == "delete_one":
                result = await collection.delete_one(filter_doc)
            else:
                # delete_many
                result = await collection.delete_many(filter_doc)

            return {
                "status": "success",
                "deleted_count": result.deleted_count
            }

        else:
            raise ValueError(f"Unsupported operation: {operation}")
