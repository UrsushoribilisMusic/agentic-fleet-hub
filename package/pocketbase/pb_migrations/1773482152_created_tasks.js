/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const collection = new Collection({
    "id": "tw44vd067pqost4",
    "created": "2026-03-14 09:55:52.845Z",
    "updated": "2026-03-14 09:55:52.845Z",
    "name": "tasks",
    "type": "base",
    "system": false,
    "schema": [
      {
        "system": false,
        "id": "nxigymhr",
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
        "id": "ih3z7g70",
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
        "id": "jyzmhpru",
        "name": "status",
        "type": "select",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "maxSelect": 1,
          "values": [
            "backlog",
            "todo",
            "in_progress",
            "peer_review",
            "waiting_human",
            "approved"
          ]
        }
      },
      {
        "system": false,
        "id": "allsgg7a",
        "name": "assigned_agent",
        "type": "select",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "maxSelect": 1,
          "values": [
            "scout",
            "echo",
            "closer",
            "clau",
            "gem",
            "codi"
          ]
        }
      },
      {
        "system": false,
        "id": "pxwrujax",
        "name": "goal_id",
        "type": "relation",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "collectionId": "spyihgln4uxuamd",
          "cascadeDelete": false,
          "minSelect": null,
          "maxSelect": 1,
          "displayFields": null
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
  const collection = dao.findCollectionByNameOrId("tw44vd067pqost4");

  return dao.deleteCollection(collection);
})
