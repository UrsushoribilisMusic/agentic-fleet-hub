/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("tw44vd067pqost4")

  // update
  collection.schema.addField(new SchemaField({
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
        "codi",
        "misty"
      ]
    }
  }))

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("tw44vd067pqost4")

  // update
  collection.schema.addField(new SchemaField({
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
  }))

  return dao.saveCollection(collection)
})
