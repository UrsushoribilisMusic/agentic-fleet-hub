/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const collection = new Collection({
    "id": "z7sxq1ff8wytgge",
    "created": "2026-03-14 09:55:52.864Z",
    "updated": "2026-03-14 09:55:52.864Z",
    "name": "lessons",
    "type": "base",
    "system": false,
    "schema": [
      {
        "system": false,
        "id": "htbsq1ju",
        "name": "title",
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
        "id": "tx0y8eat",
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
        "id": "tkuztuv9",
        "name": "category",
        "type": "select",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "maxSelect": 1,
          "values": [
            "architecture",
            "tooling",
            "integration",
            "workflow",
            "gotcha",
            "anti-pattern"
          ]
        }
      },
      {
        "system": false,
        "id": "act1scsh",
        "name": "confidence",
        "type": "select",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "maxSelect": 1,
          "values": [
            "high",
            "medium",
            "low"
          ]
        }
      },
      {
        "system": false,
        "id": "mqpdn6fs",
        "name": "status",
        "type": "select",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {
          "maxSelect": 1,
          "values": [
            "pending_review",
            "active",
            "superseded"
          ]
        }
      },
      {
        "system": false,
        "id": "z0w5sro2",
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
        "id": "nmzwrgdf",
        "name": "project",
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
  const collection = dao.findCollectionByNameOrId("z7sxq1ff8wytgge");

  return dao.deleteCollection(collection);
})
