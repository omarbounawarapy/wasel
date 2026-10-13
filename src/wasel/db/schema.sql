-- Opened per thread with:
--   PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON; PRAGMA busy_timeout=5000; PRAGMA synchronous=NORMAL;
-- Timestamps: UTC ISO-8601 'YYYY-MM-DDTHH:MM:SS.ffffffZ' written ONLY by wasel.clock.utc_iso().
-- IDs: ULID text. No migrations: the DB is rebuilt from this file (SEED_ON_BOOT).

-- ---------------------------------------------------------------- reference data
CREATE TABLE catalog (                         -- mirror of data/catalog.yaml, upserted on every boot
  product_id   TEXT PRIMARY KEY,
  name         TEXT NOT NULL,
  aliases_json TEXT NOT NULL DEFAULT '[]',
  price_tnd    REAL NOT NULL CHECK (price_tnd > 0),
  category     TEXT NOT NULL
);

-- ---------------------------------------------------------------- people and threads
CREATE TABLE customers (
  customer_id      TEXT PRIMARY KEY,
  sandbox_id       TEXT,                      -- NULL = seeded/event row; else the visitor's X-Visitor-Id
  phone_e164       TEXT UNIQUE,               -- WhatsApp only; never returned unmasked, never sent to an LLM
  external_ref     TEXT,                      -- CSV customer_id
  display_name     TEXT,
  completed_orders INTEGER NOT NULL DEFAULT 0 CHECK (completed_orders >= 0),     -- delivered + refused
  refusals_total   INTEGER NOT NULL DEFAULT 0 CHECK (refusals_total BETWEEN 0 AND completed_orders),
  first_seen_at    TEXT NOT NULL,
  last_seen_at     TEXT NOT NULL
);
CREATE UNIQUE INDEX ux_customers_extref ON customers (external_ref, COALESCE(sandbox_id, ''))
  WHERE external_ref IS NOT NULL;
CREATE INDEX ix_customers_sandbox ON customers (sandbox_id);

CREATE TABLE conversations (
  conversation_id  TEXT PRIMARY KEY,
  customer_id      TEXT NOT NULL REFERENCES customers,
  sandbox_id       TEXT,                      -- NULL = seeded/event
  channel          TEXT NOT NULL CHECK (channel IN ('whatsapp','csv','paste','simulated')),
  seed_key         TEXT,                      -- demo_seed.json conversation key; enables "Try this order"
  opened_at        TEXT NOT NULL,
  last_inbound_at  TEXT,
  last_outbound_at TEXT                       -- 24h window check
);
CREATE INDEX ix_conversations_sandbox ON conversations (sandbox_id, opened_at);

CREATE TABLE messages (
  message_id          TEXT PRIMARY KEY,
  conversation_id     TEXT NOT NULL REFERENCES conversations,
  channel_message_id  TEXT UNIQUE,            -- WhatsApp wamid; dedupe key (NULL otherwise)
  direction           TEXT NOT NULL CHECK (direction IN ('inbound','outbound')),
  author              TEXT NOT NULL CHECK (author IN ('customer','seller','ai')),
  origin              TEXT NOT NULL CHECK (origin IN ('whatsapp','csv','paste','simulated','seed','dashboard')),
  kind                TEXT NOT NULL CHECK (kind IN ('text','audio','location','image','interactive','unsupported')),
  text                TEXT,
  canonical_text      TEXT,                   -- author='ai': static template text; the only text in [SELLER]
  template_id         TEXT CHECK (template_id IN ('T_CONFIRM','T_ADDRESS','T_PREPAY','T_ACK')),
  transcript          TEXT,
  location_lat        REAL,
  location_lng        REAL,
  reply_to_message_id TEXT REFERENCES messages,
  provider_ts         TEXT NOT NULL,
  received_at         TEXT NOT NULL,
  delivery_status     TEXT CHECK (delivery_status IN ('queued','sent','delivered','read','failed')),
  raw_payload         TEXT,                   -- debug only; never returned, never exported, never committed
  CHECK ((direction = 'inbound') = (author = 'customer')),
  CHECK (author <> 'ai' OR (template_id IS NOT NULL AND canonical_text IS NOT NULL)),
  CHECK (kind <> 'location' OR (location_lat IS NOT NULL AND location_lng IS NOT NULL))
);
CREATE INDEX ix_messages_conv_ts ON messages (conversation_id, provider_ts);

-- ---------------------------------------------------------------- orders
CREATE TABLE orders (
  order_id              TEXT PRIMARY KEY,
  order_no              INTEGER NOT NULL UNIQUE,   -- UI shows '#'||order_no; seed starts at 2601; new = MAX+1 in the write txn
  conversation_id       TEXT NOT NULL REFERENCES conversations,
  customer_id           TEXT NOT NULL REFERENCES customers,
  sandbox_id            TEXT,                      -- copied from the conversation
  status                TEXT NOT NULL DEFAULT 'collecting'
                          CHECK (status IN ('collecting','awaiting_reply','needs_review','ready_to_ship',
                                            'shipped','delivered','refused','cancelled')),
  product_id            TEXT REFERENCES catalog,
  product_name          TEXT,
  quantity              INTEGER CHECK (quantity BETWEEN 1 AND 50),
  price_tnd             REAL CHECK (price_tnd >= 0),
  zone                  TEXT CHECK (zone IN ('urban','suburban','rural')),
  zone_source           TEXT NOT NULL DEFAULT 'default' CHECK (zone_source IN ('csv','gazetteer','default')),
  address_text          TEXT,
  language              TEXT CHECK (language IN ('fr','ar','darija_arabic_script','arabizi','mixed')),
  structured_json       TEXT NOT NULL DEFAULT '{}',   -- seller-entered StructuredFields, verbatim
  current_assessment_id TEXT REFERENCES risk_assessments DEFERRABLE INITIALLY DEFERRED,
  auto_messages_sent    INTEGER NOT NULL DEFAULT 0 CHECK (auto_messages_sent BETWEEN 0 AND 2),
  awaiting_reply_since  TEXT,                      -- set when a draft is sent (drives no_reply_timeout)
  seller_approved_at    TEXT,                      -- set by 'approve'; keeps ready_to_ship across soft rescores
  pending_rescore_at    TEXT,                      -- debounce slot
  pending_trigger       TEXT CHECK (pending_trigger IN ('initial','customer_reply','no_reply_timeout','manual')),
  rescore_state         TEXT NOT NULL DEFAULT 'idle'
                          CHECK (rescore_state IN ('idle','debouncing','scoring','drafting')),
  opened_at             TEXT NOT NULL,
  updated_at            TEXT NOT NULL,
  CHECK ((pending_rescore_at IS NULL) = (pending_trigger IS NULL))
);
CREATE UNIQUE INDEX ux_orders_one_open ON orders (conversation_id)
  WHERE status IN ('collecting','awaiting_reply','needs_review','ready_to_ship');      -- at most one open order per conversation
CREATE INDEX ix_orders_pending  ON orders (pending_rescore_at) WHERE pending_rescore_at IS NOT NULL;
CREATE INDEX ix_orders_awaiting ON orders (awaiting_reply_since) WHERE status = 'awaiting_reply';
CREATE INDEX ix_orders_sandbox  ON orders (sandbox_id, updated_at);

CREATE TABLE order_messages (
  order_id   TEXT NOT NULL REFERENCES orders,
  message_id TEXT NOT NULL REFERENCES messages,
  PRIMARY KEY (order_id, message_id)
);
CREATE INDEX ix_order_messages_msg ON order_messages (message_id);

-- ---------------------------------------------------------------- LLM layer
CREATE TABLE extraction_cache (                -- no FK: survives reset and purge; seeded from data/seed/extraction_cache.jsonl
  input_hash     TEXT PRIMARY KEY,             -- sha256(PROMPT_VERSION|schema_name|normalized window incl. [SELLER])
  prompt_version TEXT NOT NULL,
  provider       TEXT NOT NULL CHECK (provider IN ('groq','gemini')),
  model          TEXT NOT NULL,
  origin_path    TEXT NOT NULL CHECK (origin_path IN ('llm','fallback_model','fallback_provider')),
  is_primary     INTEGER NOT NULL CHECK (is_primary IN (0,1)),   -- upsert replaces only if new.is_primary >= old
  extraction_json TEXT NOT NULL,               -- after repair + evidence + tone gate; evidence uses msg_idx
  created_at     TEXT NOT NULL,
  sandbox_id     TEXT                          -- visitor whose text produced the row; purged with the sandbox. NULL = seed file or event data
);

CREATE TABLE extraction_runs (                 -- append-only; one row per scoring run that produced/reused an extraction
  extraction_id       TEXT PRIMARY KEY,
  order_id            TEXT NOT NULL REFERENCES orders,
  input_message_ids   TEXT NOT NULL,           -- JSON array; msg_idx k -> element k
  input_hash          TEXT NOT NULL,
  provider            TEXT NOT NULL CHECK (provider IN ('groq','gemini','cascade','rules')),
  model               TEXT NOT NULL,
  prompt_version      TEXT NOT NULL,
  cache_hit           INTEGER NOT NULL DEFAULT 0 CHECK (cache_hit IN (0,1)),
  attempts_json       TEXT NOT NULL DEFAULT '[]',
  output_json         TEXT,                    -- raw provider text; NULL on cache hit / cascade / rules
  validated_json      TEXT,                    -- final extraction used for features
  spans_json          TEXT NOT NULL DEFAULT '[]',   -- [{message_id,start,end,kind,code,quote}], code points, original text
  valid               INTEGER NOT NULL CHECK (valid IN (0,1)),
  dropped_flags       INTEGER NOT NULL DEFAULT 0,
  dropped_quotes      INTEGER NOT NULL DEFAULT 0,
  injection_suspected INTEGER NOT NULL DEFAULT 0 CHECK (injection_suspected IN (0,1)),
  error               TEXT,
  latency_ms          INTEGER,
  tokens_in           INTEGER,
  tokens_out          INTEGER,
  created_at          TEXT NOT NULL,
  endpoint            TEXT                     -- deployment that answered ('groq', 'self-hosted', ...); open set, NULL = not recorded
);
CREATE INDEX ix_extraction_runs_order ON extraction_runs (order_id, created_at);

CREATE TABLE llm_usage (                       -- one row per provider attempt; drives caps and /api/health
  usage_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  ts         TEXT NOT NULL,
  day        TEXT NOT NULL,                    -- UTC 'YYYY-MM-DD'
  sandbox_id TEXT,                             -- NULL = seeded/event/admin traffic
  order_id   TEXT,                             -- no FK: usage outlives purged orders (cap accounting)
  role       TEXT NOT NULL CHECK (role IN ('extract','rewrite','judge')),
  provider   TEXT NOT NULL CHECK (provider IN ('groq','gemini')),
  model      TEXT NOT NULL,
  outcome    TEXT NOT NULL CHECK (outcome IN ('ok','rate_limited','down','timeout','schema_rejected','truncated','parse_error')),
  tokens_in  INTEGER,
  tokens_out INTEGER,
  latency_ms INTEGER NOT NULL,
  endpoint   TEXT                              -- deployment attempted ('groq', 'self-hosted', ...); open set, NULL = not recorded
);
CREATE INDEX ix_llm_usage_day     ON llm_usage (day);
CREATE INDEX ix_llm_usage_sandbox ON llm_usage (sandbox_id, ts);

-- ---------------------------------------------------------------- decisions
CREATE TABLE risk_assessments (                -- append-only; a rescore inserts version n+1
  assessment_id           TEXT PRIMARY KEY,
  order_id                TEXT NOT NULL REFERENCES orders,
  version                 INTEGER NOT NULL CHECK (version >= 1),
  trigger                 TEXT NOT NULL CHECK (trigger IN ('initial','customer_reply','no_reply_timeout','manual')),
  extraction_id           TEXT REFERENCES extraction_runs,   -- NULL only if the rules extractor produced no row
  path                    TEXT NOT NULL CHECK (path IN ('llm','fallback_model','fallback_provider',
                                                        'cascade_ack','cascade_cache','rules')),
  features_json           TEXT NOT NULL,     -- exactly FEATURES (6 keys)
  context_json            TEXT NOT NULL,     -- has_geo_pin, product_id, category, history, imputed[], zone_source, clarity, tone, language
  model_score             REAL NOT NULL CHECK (model_score BETWEEN 0 AND 100),
  confirmation            TEXT NOT NULL CHECK (confirmation IN ('none','confirmed','declined','reschedule','ambiguous')),
  adjustments_json        TEXT NOT NULL,     -- [Adjustment]
  resolved_flags_json     TEXT NOT NULL DEFAULT '[]',
  flags_json              TEXT NOT NULL DEFAULT '[]',   -- [FlagView]
  final_score             INTEGER NOT NULL CHECK (final_score BETWEEN 0 AND 100),  -- declined: scored normally, never NULL
  tier                    TEXT NOT NULL CHECK (tier IN ('low','medium','high')),
  action                  TEXT NOT NULL CHECK (action IN ('ship','confirm','prepay','review','cancelled')),
  confidence              TEXT NOT NULL CHECK (confidence IN ('high','low')),
  confidence_reasons_json TEXT NOT NULL DEFAULT '[]',
  reason                  TEXT NOT NULL,
  reason_short            TEXT NOT NULL,
  reason_diff             TEXT,
  top_factors_json        TEXT NOT NULL,
  template_id             TEXT CHECK (template_id IN ('T_CONFIRM','T_ADDRESS','T_PREPAY','T_ACK')),
  is_order_change         INTEGER NOT NULL DEFAULT 0 CHECK (is_order_change IN (0,1)),
  classifier_version      TEXT NOT NULL,
  config_hash             TEXT NOT NULL,
  prompt_version          TEXT NOT NULL,
  created_at              TEXT NOT NULL,
  UNIQUE (order_id, version),
  CHECK ((confirmation = 'declined') = (action = 'cancelled'))
);

CREATE TABLE outbound_drafts (
  draft_id        TEXT PRIMARY KEY,
  order_id        TEXT NOT NULL REFERENCES orders,
  assessment_id   TEXT NOT NULL REFERENCES risk_assessments,
  template_id     TEXT NOT NULL CHECK (template_id IN ('T_CONFIRM','T_ADDRESS','T_PREPAY','T_ACK')),
  language        TEXT NOT NULL,
  canonical_text  TEXT NOT NULL,             -- static template rendered with slots
  rendered_text   TEXT NOT NULL,             -- what is shown/sent (rewrite if approved, else canonical_text)
  source          TEXT NOT NULL CHECK (source IN ('llm_rewrite','static_template')),
  prefilter_json  TEXT NOT NULL,
  judge_json      TEXT,                      -- NULL when static; {"unavailable":true} when the judge failed closed
  route           TEXT NOT NULL CHECK (route IN ('auto_send','needs_review','blocked')),
  decided_by      TEXT CHECK (decided_by IN ('system','human')),
  sent_message_id TEXT REFERENCES messages,
  sent_at         TEXT,
  sending_at      TEXT,                      -- claimed by one send attempt (commands.send_draft); NULL when free
  delivery        TEXT CHECK (delivery IN ('whatsapp_sent','recorded_only')),
  created_at      TEXT NOT NULL,
  CHECK ((sent_message_id IS NULL) = (sent_at IS NULL)),
  CHECK (source = 'static_template' OR judge_json IS NOT NULL)
);
CREATE UNIQUE INDEX ux_drafts_one_unsent ON outbound_drafts (order_id) WHERE sent_message_id IS NULL;

-- ---------------------------------------------------------------- activity feed
CREATE TABLE events (
  seq        INTEGER PRIMARY KEY AUTOINCREMENT,   -- monotonic cursor for GET /api/events?after=
  ts         TEXT NOT NULL,
  type       TEXT NOT NULL,        -- message.received, order.rescored, draft.created, draft.sent, draft.judged,
                                   -- draft.recorded_for_simulation, llm.fallback, llm.cap_reached, cache.hit,
                                   -- cascade.hit, evidence.dropped, flags.resolved, webhook.rejected, sandbox.created, error
  level      TEXT NOT NULL DEFAULT 'info' CHECK (level IN ('info','success','warning','error')),
  order_id   TEXT,                 -- no FK (purge deletes explicitly)
  sandbox_id TEXT,
  entity_id  TEXT,
  payload    TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX ix_events_order   ON events (order_id, seq);
CREATE INDEX ix_events_sandbox ON events (sandbox_id, seq);
