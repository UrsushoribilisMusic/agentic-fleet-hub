/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("tw44vd067pqost4")

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "reassign_cnt",
    "name": "reassignment_count",
    "type": "number",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "min": 0,
      "max": null,
      "noDecimal": true
    }
  }))

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "last_reassign",
    "name": "last_reassignment_at",
    "type": "date",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "min": "",
      "max": ""
    }
  }))

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "dzq9shh3",
    "name": "scratchpad",
    "type": "json",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "maxSize": 2000000
    }
  }))

  // update
  collection.schema.addField(new SchemaField({
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
        "waiting_human_notified",
        "approved",
        "blocked"
      ]
    }
  }))

  // update
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "skill999",
    "name": "required_skills",
    "type": "json",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "maxSize": 2000000
    }
  }))

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("tw44vd067pqost4")

  // remove
  collection.schema.removeField("reassign_cnt")

  // remove
  collection.schema.removeField("last_reassign")

  // remove
  collection.schema.removeField("dzq9shh3")

  // update
  collection.schema.addField(new SchemaField({
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
        "approved",
        "waiting_human_notified"
      ]
    }
  }))

  // update
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "skill999",
    "name": "required_skills",
    "type": "json",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "maxSize": 0
    }
  }))

  return dao.saveCollection(collection)
})
