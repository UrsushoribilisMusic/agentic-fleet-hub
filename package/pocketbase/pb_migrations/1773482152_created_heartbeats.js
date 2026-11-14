/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const collection = new Collection({
    "id": "0wr1cowjw13t7cp",
    "created": "2026-03-14 09:55:52.858Z",
    "updated": "2026-03-14 09:55:52.858Z",
    "name": "heartbeats",
    "type": "base",
    "system": false,
    "schema": [
      {
        "system": false,
        "id": "rrkuia15",
        "name": "agent",
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
        "id": "y8xn6s0y",
        "name": "status",
        "type": "select",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "maxSelect": 1,
          "values": [
            "working",
            "idle",
            "blocked"
          ]
        }
      },
      {
        "system": false,
        "id": "0kgbmewa",
        "name": "note",
        "type": "text",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "min": null,
          "max": null,
          "pattern": ""
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
  const collection = dao.findCollectionByNameOrId("0wr1cowjw13t7cp");

  return dao.deleteCollection(collection);
})
