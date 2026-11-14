/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("z7sxq1ff8wytgge")

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "snonuefq",
    "name": "decision",
    "type": "text",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "min": null,
      "max": null,
      "pattern": ""
    }
  }))

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "a0ucft6v",
    "name": "rationale",
    "type": "text",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "min": null,
      "max": null,
      "pattern": ""
    }
  }))

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "zegvsbgc",
    "name": "outcome",
    "type": "text",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "min": null,
      "max": null,
      "pattern": ""
    }
  }))

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "dinx8kwd",
    "name": "confidence_score",
    "type": "number",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "min": 0,
      "max": 100,
      "noDecimal": false
    }
  }))

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("z7sxq1ff8wytgge")

  // remove
  collection.schema.removeField("snonuefq")

  // remove
  collection.schema.removeField("a0ucft6v")

  // remove
  collection.schema.removeField("zegvsbgc")

  // remove
  collection.schema.removeField("dinx8kwd")

  return dao.saveCollection(collection)
})
