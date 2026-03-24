from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase


class QueryService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def query(
            self,
            collection: str,
            filter: Optional[Dict[Any, Any]] = None,
            projection: Optional[Dict[Any, Any]] = None,
            sort: Optional[List] = None,
            limit: Optional[int] = None,
            skip: Optional[int] = None
    ) -> Dict[str, Any]:
        collections = await self.db.list_collection_names()
        if collection not in collections:
            raise ValueError(f"Collection '{collection}' does not exist")

        # 构建查询
        query_filter = filter or {}
        cursor = self.db[collection].find(query_filter, projection)

        if sort:
            cursor = cursor.sort(sort)

        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)

        data = await cursor.to_list(length=limit)
        total = await self.db[collection].count_documents(query_filter)

        for item in data:
            if "_id" in item:
                item["_id"] = str(item["_id"])

        return {"data": data, "total": total}
