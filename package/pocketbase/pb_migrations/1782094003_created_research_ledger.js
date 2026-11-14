/// <reference path="../pb_data/types.d.ts" />
// FCP-7: Research Workbench source and claim ledger
// Supports prospect intelligence, tech shorts, public articles, and sales assets.
// Enforces source discipline and evidence preservation.

const SOURCE_TYPES = [
  "primary",
  "secondary",
  "tertiary",
  "interview",
  "internal_telemetry",
  "other",
];

const RELIABILITY_TIERS = [
  "high",
  "moderate",
  "low",
  "unknown",
];

const CONFIDENCE_TIERS = [
  "high",
  "moderate",
  "low",
  "speculative",
];

const VERIFICATION_STATUSES = [
  "unverified",
  "verified",
  "contested",
  "refuted",
];

function textField(id, name, required, presentable) {
  return new SchemaField({
    system: false,
    id: id,
    name: name,
    type: "text",
    required: !!required,
    presentable: !!presentable,
    unique: false,
    options: {
      min: null,
      max: null,
      pattern: "",
    },
  });
}

function selectField(id, name, values, required) {
  return new SchemaField({
    system: false,
    id: id,
    name: name,
    type: "select",
    required: !!required,
    presentable: false,
    unique: false,
    options: {
      maxSelect: 1,
      values: values,
    },
  });
}

function boolField(id, name) {
  return new SchemaField({
    system: false,
    id: id,
    name: name,
    type: "bool",
    required: false,
    presentable: false,
    unique: false,
    options: {},
  });
}

function relationField(id, name, collectionId, required) {
  return new SchemaField({
    system: false,
    id: id,
    name: name,
    type: "relation",
    required: !!required,
    presentable: false,
    unique: false,
    options: {
      collectionId: collectionId,
      cascadeDelete: false,
      minSelect: null,
      maxSelect: 1,
      displayFields: ["title", "name", "extracted_claim"],
    },
  });
}

function findCollectionOrNull(dao, nameOrId) {
  try {
    return dao.findCollectionByNameOrId(nameOrId);
  } catch (_) {
    return null;
  }
}

function createResearchSourcesCollection(dao, goalsCollection) {
  let existing = findCollectionOrNull(dao, "research_sources");
  if (existing) {
    return existing;
  }

  const collection = new Collection({
    id: "rsources0000001",
    name: "research_sources",
    type: "base",
    system: false,
    schema: [
      relationField("rsrc_goal_id", "goal_id", goalsCollection.id, true),
      textField("rsrc_url", "url", true, false),
      textField("rsrc_title", "title", true, true),
      textField("rsrc_author", "author", false, false),
      selectField("rsrc_type", "source_type", SOURCE_TYPES, true),
      selectField("rsrc_rel", "reliability", RELIABILITY_TIERS, true),
      textField("rsrc_agent", "agent", false, false),
      textField("rsrc_notes", "notes", false, false),
    ],
    indexes: [
      "CREATE INDEX idx_research_sources_goal ON research_sources (goal_id)",
      "CREATE INDEX idx_research_sources_url ON research_sources (url)",
      "CREATE INDEX idx_research_sources_type ON research_sources (source_type)",
    ],
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: null,
    options: {},
  });

  dao.saveCollection(collection);
  return collection;
}

function createResearchClaimsCollection(dao, goalsCollection, sourcesCollection) {
  if (findCollectionOrNull(dao, "research_claims")) {
    return;
  }

  const collection = new Collection({
    id: "rclaims00000001",
    name: "research_claims",
    type: "base",
    system: false,
    schema: [
      relationField("rclaim_goal_id", "goal_id", goalsCollection.id, true),
      relationField("rclaim_src_id", "source_id", sourcesCollection.id, false),
      textField("rclaim_url", "source_url", false, false),
      textField("rclaim_stitle", "source_title", false, false),
      selectField("rclaim_stype", "source_type", SOURCE_TYPES, false),
      textField("rclaim_claim", "extracted_claim", true, true),
      textField("rclaim_quote", "quote_snippet", false, false),
      selectField("rclaim_conf", "confidence", CONFIDENCE_TIERS, true),
      selectField("rclaim_vstatus", "verification_status", VERIFICATION_STATUSES, true),
      boolField("rclaim_public", "usable_in_public_copy"),
      boolField("rclaim_review", "needs_human_review"),
      textField("rclaim_revby", "reviewed_by", false, false),
      textField("rclaim_agent", "agent", false, false),
      textField("rclaim_notes", "notes", false, false),
    ],
    indexes: [
      "CREATE INDEX idx_research_claims_goal ON research_claims (goal_id)",
      "CREATE INDEX idx_research_claims_source ON research_claims (source_id)",
      "CREATE INDEX idx_research_claims_conf ON research_claims (confidence)",
      "CREATE INDEX idx_research_claims_vstatus ON research_claims (verification_status)",
      "CREATE INDEX idx_research_claims_public ON research_claims (usable_in_public_copy)",
    ],
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: null,
    options: {},
  });

  dao.saveCollection(collection);
}

migrate((db) => {
  const dao = new Dao(db);
  const goalsCollection = findCollectionOrNull(dao, "goals");
  if (!goalsCollection) {
    return; // goals must exist before research collections
  }

  const sourcesCollection = createResearchSourcesCollection(dao, goalsCollection);
  createResearchClaimsCollection(dao, goalsCollection, sourcesCollection);
}, (db) => {
  const dao = new Dao(db);

  const claims = findCollectionOrNull(dao, "research_claims");
  if (claims) {
    dao.deleteCollection(claims);
  }

  const sources = findCollectionOrNull(dao, "research_sources");
  if (sources) {
    dao.deleteCollection(sources);
  }
});
