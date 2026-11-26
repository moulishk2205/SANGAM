-- SANGAM database schema (SQLite dialect).
-- Generated from src/nmc/db/models.py via SQLAlchemy create_all — the same path the API takes on startup.
-- Nothing in the schema is SQLite-specific; point DATABASE_URL at PostgreSQL and the same models apply.


CREATE TABLE organisations (
	id VARCHAR(32) NOT NULL, 
	name VARCHAR(160) NOT NULL, 
	code_prefix VARCHAR(32) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE item_class_rules (
	item_class VARCHAR(60) NOT NULL, 
	label VARCHAR(160) NOT NULL, 
	extra_critical JSON NOT NULL, 
	bars_auto_match BOOLEAN NOT NULL, 
	requires_certification BOOLEAN NOT NULL, 
	basis VARCHAR(200) NOT NULL, 
	PRIMARY KEY (item_class)
);

CREATE TABLE users (
	id VARCHAR(40) NOT NULL, 
	email VARCHAR(200) NOT NULL, 
	name VARCHAR(160) NOT NULL, 
	role VARCHAR(9) NOT NULL, 
	org_id VARCHAR(32) NOT NULL, 
	commodity_scope JSON NOT NULL, 
	class_certifications JSON NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	active BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (email), 
	FOREIGN KEY(org_id) REFERENCES organisations (id)
);

CREATE TABLE sessions (
	token VARCHAR(64) NOT NULL, 
	user_id VARCHAR(40) NOT NULL, 
	created_at DATETIME NOT NULL, 
	expires_at DATETIME NOT NULL, 
	revoked BOOLEAN NOT NULL, 
	PRIMARY KEY (token), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE canonical_materials (
	id VARCHAR(40) NOT NULL, 
	item_name VARCHAR(120) NOT NULL, 
	canonical_text TEXT NOT NULL, 
	attributes JSON NOT NULL, 
	standard_description TEXT NOT NULL, 
	family VARCHAR(40) NOT NULL, 
	item_class VARCHAR(60) NOT NULL, 
	spec_standard VARCHAR(80) NOT NULL, 
	spec_revision VARCHAR(40) NOT NULL, 
	superseded_by VARCHAR(40), 
	created_at DATETIME NOT NULL, 
	created_by VARCHAR(40), 
	PRIMARY KEY (id), 
	FOREIGN KEY(superseded_by) REFERENCES canonical_materials (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE TABLE audit_events (
	id VARCHAR(40) NOT NULL, 
	at DATETIME NOT NULL, 
	actor_id VARCHAR(40), 
	action VARCHAR(80) NOT NULL, 
	subject VARCHAR(80) NOT NULL, 
	detail JSON NOT NULL, 
	ip VARCHAR(64) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id)
);

CREATE TABLE releases (
	id VARCHAR(40) NOT NULL, 
	gazetteer_version VARCHAR(40) NOT NULL, 
	template_version VARCHAR(40) NOT NULL, 
	model_version VARCHAR(80) NOT NULL, 
	promoted_at DATETIME, 
	promoted_by VARCHAR(40), 
	notes TEXT NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(promoted_by) REFERENCES users (id)
);

CREATE TABLE ingest_jobs (
	id VARCHAR(40) NOT NULL, 
	org_id VARCHAR(32) NOT NULL, 
	filename VARCHAR(255) NOT NULL, 
	status VARCHAR(7) NOT NULL, 
	total INTEGER NOT NULL, 
	processed INTEGER NOT NULL, 
	accepted INTEGER NOT NULL, 
	rejected INTEGER NOT NULL, 
	error TEXT NOT NULL, 
	created_by VARCHAR(40), 
	created_at DATETIME NOT NULL, 
	finished_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organisations (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE TABLE source_records (
	id VARCHAR(40) NOT NULL, 
	org_id VARCHAR(32) NOT NULL, 
	org_code VARCHAR(64) NOT NULL, 
	raw_description TEXT NOT NULL, 
	normalised TEXT NOT NULL, 
	item_name VARCHAR(120) NOT NULL, 
	attributes JSON NOT NULL, 
	provenance VARCHAR(40) NOT NULL, 
	ingest_job_id VARCHAR(40), 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organisations (id), 
	FOREIGN KEY(ingest_job_id) REFERENCES ingest_jobs (id)
);

CREATE TABLE mappings (
	id VARCHAR(40) NOT NULL, 
	source_record_id VARCHAR(40) NOT NULL, 
	canonical_id VARCHAR(40) NOT NULL, 
	status VARCHAR(10) NOT NULL, 
	confidence FLOAT NOT NULL, 
	decided_by_engine VARCHAR(40) NOT NULL, 
	effective_from DATETIME NOT NULL, 
	effective_to DATETIME, 
	superseded_by VARCHAR(40), 
	proposed_at DATETIME NOT NULL, 
	proposed_by VARCHAR(40), 
	PRIMARY KEY (id), 
	FOREIGN KEY(source_record_id) REFERENCES source_records (id), 
	FOREIGN KEY(canonical_id) REFERENCES canonical_materials (id), 
	FOREIGN KEY(superseded_by) REFERENCES mappings (id), 
	FOREIGN KEY(proposed_by) REFERENCES users (id)
);

CREATE TABLE procurement_records (
	id VARCHAR(40) NOT NULL, 
	org_id VARCHAR(32) NOT NULL, 
	source_record_id VARCHAR(40) NOT NULL, 
	quantity FLOAT NOT NULL, 
	uom VARCHAR(12) NOT NULL, 
	unit_price_paise INTEGER NOT NULL, 
	line_value_paise INTEGER NOT NULL, 
	ordered_on DATETIME NOT NULL, 
	supplier VARCHAR(120) NOT NULL, 
	plant VARCHAR(80) NOT NULL, 
	service_class VARCHAR(40) NOT NULL, 
	po_number VARCHAR(40) NOT NULL, 
	provenance VARCHAR(40) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(org_id) REFERENCES organisations (id), 
	FOREIGN KEY(source_record_id) REFERENCES source_records (id)
);

CREATE TABLE decisions (
	seq INTEGER NOT NULL, 
	id VARCHAR(40) NOT NULL, 
	kind VARCHAR(9) NOT NULL, 
	mapping_id VARCHAR(40), 
	source_record_id VARCHAR(40), 
	canonical_id VARCHAR(40), 
	actor_id VARCHAR(40), 
	actor_role VARCHAR(40) NOT NULL, 
	actor_scope JSON NOT NULL, 
	note TEXT NOT NULL, 
	evidence JSON NOT NULL, 
	gazetteer_version VARCHAR(40) NOT NULL, 
	template_version VARCHAR(40) NOT NULL, 
	model_version VARCHAR(80) NOT NULL, 
	prev_hash VARCHAR(64) NOT NULL, 
	hash VARCHAR(64) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (seq), 
	FOREIGN KEY(mapping_id) REFERENCES mappings (id), 
	FOREIGN KEY(source_record_id) REFERENCES source_records (id), 
	FOREIGN KEY(canonical_id) REFERENCES canonical_materials (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id)
);
CREATE INDEX ix_sessions_user_id ON sessions (user_id);
CREATE INDEX ix_canonical_materials_item_name ON canonical_materials (item_name);
CREATE INDEX ix_canonical_materials_family ON canonical_materials (family);
CREATE INDEX ix_canonical_materials_item_class ON canonical_materials (item_class);
CREATE INDEX ix_audit_events_at ON audit_events (at);
CREATE INDEX ix_audit_events_action ON audit_events (action);
CREATE INDEX ix_audit_events_actor_id ON audit_events (actor_id);
CREATE INDEX ix_ingest_jobs_status ON ingest_jobs (status);
CREATE INDEX ix_source_org_code ON source_records (org_id, org_code);
CREATE INDEX ix_source_records_org_id ON source_records (org_id);
CREATE INDEX ix_source_records_item_name ON source_records (item_name);
CREATE INDEX ix_mappings_status ON mappings (status);
CREATE INDEX ix_mappings_source_record_id ON mappings (source_record_id);
CREATE INDEX ix_mappings_canonical_id ON mappings (canonical_id);
CREATE INDEX ix_mapping_live ON mappings (source_record_id, status);
CREATE INDEX ix_procurement_records_service_class ON procurement_records (service_class);
CREATE INDEX ix_procurement_records_source_record_id ON procurement_records (source_record_id);
CREATE INDEX ix_procurement_records_org_id ON procurement_records (org_id);
CREATE INDEX ix_procurement_records_ordered_on ON procurement_records (ordered_on);
CREATE INDEX ix_decisions_hash ON decisions (hash);
CREATE INDEX ix_decisions_mapping_id ON decisions (mapping_id);
CREATE UNIQUE INDEX ix_decisions_id ON decisions (id);
CREATE INDEX ix_decisions_kind ON decisions (kind);
