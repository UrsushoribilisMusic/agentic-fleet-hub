/// <reference path="../pb_data/types.d.ts" />

const GOAL_STATUSES = [
  "draft",
  "council_open",
  "synthesis_ready",
  "waiting_human",
  "approved",
  "rejected",
  "ticketed",
  "closed",
];

const OUTPUT_TYPES = [
  "code",
  "research",
  "sales_asset",
  "dashboard",
  "content",
  "experiment",
  "mixed",
];

const COUNCIL_ROLES = [
  "planner",
  "skeptic",
  "researcher",
  "architect",
  "executor",
  "reviewer",
  "synthesizer",
];

const CONFIDENCE_TIERS = [
  "high",
  "moderate",
  "low",
  "speculative",
];

const BRIEF_STATUSES = [
  "draft",
  "waiting_human",
  "approved",
  "rejected",
  "ticketed",
];

function textField(id, name, required) {
  return new SchemaField({
    system: false,
    id: id,
    name: name,
    type: "text",
    required: !!required,
    presentable: name === "title" || name === "summary",
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

function jsonField(id, name) {
  return new SchemaField({
    system: false,
    id: id,
    name: name,
    type: "json",
    required: false,
    presentable: false,
    unique: false,
    options: {
      maxSize: 2000000,
    },
  });
}

function dateField(id, name) {
  return new SchemaField({
    system: false,
    id: id,
    name: name,
    type: "date",
    required: false,
    presentable: false,
    unique: false,
    options: {
      min: "",
      max: "",
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

function numberField(id, name, min, max) {
  return new SchemaField({
    system: false,
    id: id,
    name: name,
    type: "number",
    required: true,
    presentable: false,
    unique: false,
    options: {
      min: min,
      max: max,
      noDecimal: true,
    },
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
      displayFields: ["title"],
    },
  });
}

function replaceField(collection, field) {
  try {
    const existing = collection.schema.getFieldByName(field.name);
    field.id = existing.id;
  } catch (_) {
    // field does not exist yet
  }
  collection.schema.addField(field);
}

function findCollectionOrNull(dao, nameOrId) {
  try {
    return dao.findCollectionByNameOrId(nameOrId);
  } catch (_) {
    return null;
  }
}

function saveGoalsCollection(dao) {
  let collection = findCollectionOrNull(dao, "goals");

  if (!collection) {
    collection = new Collection({
      id: "councilgoals01",
      name: "goals",
      type: "base",
      system: false,
      schema: [],
      indexes: [],
      listRule: "",
      viewRule: "",
      createRule: "",
      updateRule: "",
      deleteRule: null,
      options: {},
    });
  }

  [
    textField("goal_title", "title", true),
    selectField("goal_status", "status", GOAL_STATUSES, true),
    textField("goal_body", "goal", true),
    textField("goal_why_now", "why_now", false),
    textField("goal_const", "constraints", false),
    textField("goal_success", "success_criteria", false),
    dateField("goal_deadline", "deadline"),
    selectField("goal_output", "output_type", OUTPUT_TYPES, false),
    boolField("goal_research", "allow_internet_research"),
    textField("goal_owner", "owner", false),
  ].forEach((field) => replaceField(collection, field));

  collection.indexes = [
    "CREATE INDEX idx_goals_status ON goals (status)",
    "CREATE INDEX idx_goals_deadline ON goals (deadline)",
  ];

  dao.saveCollection(collection);
  return collection;
}

function createDeliberationsCollection(dao, goalsCollection) {
  if (findCollectionOrNull(dao, "deliberations")) {
    return;
  }

  const collection = new Collection({
    id: "councildelibs01",
    name: "deliberations",
    type: "base",
    system: false,
    schema: [
      relationField("del_goal_id", "goal_id", goalsCollection.id, true),
      textField("del_agent", "agent", true),
      numberField("del_round", "round", 1, 2),
      selectField("del_role", "role", COUNCIL_ROLES, true),
      textField("del_recommend", "recommendation", true),
      textField("del_risks", "risks", false),
      textField("del_rejected", "rejected_options", false),
      textField("del_questions", "open_questions", false),
      textField("del_evidence", "evidence_needed", false),
      selectField("del_conf", "confidence", CONFIDENCE_TIERS, true),
    ],
    indexes: [
      "CREATE INDEX idx_deliberations_goal_id ON deliberations (goal_id)",
      "CREATE INDEX idx_deliberations_goal_round ON deliberations (goal_id, round)",
      "CREATE INDEX idx_deliberations_agent ON deliberations (agent)",
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

function createDecisionBriefsCollection(dao, goalsCollection) {
  if (findCollectionOrNull(dao, "decision_briefs")) {
    return;
  }

  const collection = new Collection({
    id: "councilbriefs1",
    name: "decision_briefs",
    type: "base",
    system: false,
    schema: [
      relationField("brief_goal_id", "goal_id", goalsCollection.id, true),
      selectField("brief_status", "status", BRIEF_STATUSES, true),
      textField("brief_summary", "summary", true),
      textField("brief_approach", "recommended_approach", true),
      textField("brief_agree", "agreement", false),
      textField("brief_disagree", "disagreement", false),
      textField("brief_rejected", "rejected_alternatives", false),
      textField("brief_risks", "known_risks", false),
      textField("brief_questions", "open_questions_for_miguel", false),
      jsonField("brief_tickets", "ticket_plan"),
      textField("brief_dod", "definition_of_done", false),
      jsonField("brief_reviews", "review_assignments"),
      textField("brief_creator", "created_by", false),
      textField("brief_approver", "approved_by", false),
    ],
    indexes: [
      "CREATE INDEX idx_decision_briefs_goal_id ON decision_briefs (goal_id)",
      "CREATE INDEX idx_decision_briefs_status ON decision_briefs (status)",
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
  const goalsCollection = saveGoalsCollection(dao);

  createDeliberationsCollection(dao, goalsCollection);
  createDecisionBriefsCollection(dao, goalsCollection);
}, (db) => {
  const dao = new Dao(db);

  const decisionBriefs = findCollectionOrNull(dao, "decision_briefs");
  if (decisionBriefs) {
    dao.deleteCollection(decisionBriefs);
  }

  const deliberations = findCollectionOrNull(dao, "deliberations");
  if (deliberations) {
    dao.deleteCollection(deliberations);
  }

  const goals = findCollectionOrNull(dao, "goals");
  if (goals) {
    [
      "goal_title",
      "goal_status",
      "goal_body",
      "goal_why_now",
      "goal_const",
      "goal_success",
      "goal_deadline",
      "goal_output",
      "goal_research",
      "goal_owner",
    ].forEach((fieldId) => {
      try {
        goals.schema.removeField(fieldId);
      } catch (_) {
        // field already absent
      }
    });
    goals.indexes = [];
    dao.saveCollection(goals);
  }
});
