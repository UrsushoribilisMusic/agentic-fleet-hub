/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const collection = new Collection({
    "id": "j0xvn7wrp7gk15f",
    "created": "2026-03-14 09:55:52.852Z",
    "updated": "2026-03-14 09:55:52.852Z",
    "name": "comments",
    "type": "base",
    "system": false,
    "schema": [
      {
        "system": false,
        "id": "0ordu6px",
        "name": "task_id",
        "type": "relation",
        "required": true,
        "presentable": false,
        "unique": false,
        "options": {
          "collectionId": "tw44vd067pqost4",
          "cascadeDelete": true,
          "minSelect": null,
          "maxSelect": 1,
          "displayFields": null
        }
      },
      {
        "system": false,
        "id": "jc8t5eb9",
        "name": "agent",
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
        "id": "1nm2xfwv",
        "name": "content",
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
        "id": "sy5xp6il",
        "name": "type",
        "type": "select",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "maxSelect": 1,
          "values": [
            "output",
            "feedback",
            "approval",
            "question",
            "flag"
          ]
        }
      },
      {
        "system": false,
        "id": "ayxmira8",
        "name": "mentions",
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
  const collection = dao.findCollectionByNameOrId("j0xvn7wrp7gk15f");

  return dao.deleteCollection(collection);
})
