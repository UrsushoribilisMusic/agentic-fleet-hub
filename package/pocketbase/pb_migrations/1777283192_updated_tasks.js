/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("tw44vd067pqost4")

  collection.indexes = [
    "CREATE UNIQUE INDEX `idx_gh_repo_issue` ON `tasks` (\n  `github_repo`,\n  `gh_issue_id`\n) WHERE gh_issue_id > 0 AND github_repo != \"\""
  ]

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "gh_repo_idx",
    "name": "github_repo",
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
    "id": "gh_url_idx",
    "name": "github_issue_url",
    "type": "url",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "exceptDomains": null,
      "onlyDomains": null
    }
  }))

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("tw44vd067pqost4")

  collection.indexes = []

  // remove
  collection.schema.removeField("gh_repo_idx")

  // remove
  collection.schema.removeField("gh_url_idx")

  return dao.saveCollection(collection)
})
