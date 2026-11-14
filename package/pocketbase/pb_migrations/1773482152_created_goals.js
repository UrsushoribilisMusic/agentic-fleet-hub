/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const collection = new Collection({
    "id": "spyihgln4uxuamd",
    "created": "2026-03-14 09:55:52.837Z",
    "updated": "2026-03-14 09:55:52.837Z",
    "name": "goals",
    "type": "base",
    "system": false,
    "schema": [
      {
        "system": false,
        "id": "0deunnlc",
        "name": "title",
        "type": "text",
        "required": true,
        "presentable": false,
        "unique": false,
        "options": {
          "min": null,
          "max": null,
          "pattern": ""
        }
      },
      {
        "system": false,
        "id": "ygtbbr6t",
        "name": "description",
        "type": "text",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "min": null,
          "max": null,
          "pattern": ""
        }
      },
      {
        "system": false,
        "id": "6io28t3n",
        "name": "assigned_agents",
        "type": "json",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "maxSize": 2000000
        }
      },
      {
        "system": false,
        "id": "mj8sbvzy",
        "name": "tasks_per_day",
        "type": "number",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "min": null,
          "max": null,
          "noDecimal": false
        }
      },
      {
        "system": false,
        "id": "sgputnwl",
        "name": "status",
        "type": "select",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "maxSelect": 1,
          "values": [
            "active",
            "paused",
            "completed"
          ]
        }
      }
    ],
    "indexes": [],
    "listRule": "",
    "viewRule": "",
    "createRule": "",
    "updateRule": "",
    "deleteRule": null,
    "options": {}
  });

  return Dao(db).saveCollection(collection);
}, (db) => {
  const dao = new Dao(db);
  const collection = dao.findCollectionByNameOrId("spyihgln4uxuamd");

  return dao.deleteCollection(collection);
})
