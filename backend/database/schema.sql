CREATE TABLE IF NOT EXISTS materials (
    id UUID PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    CONSTRAINT uq_materials_name UNIQUE (name),
    alloy_group VARCHAR(120) NOT NULL,
    density_kg_m3 DOUBLE PRECISION NOT NULL CHECK (density_kg_m3 > 0),
    electrochemical_potential_v DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_materials_name ON materials (name);

CREATE TABLE IF NOT EXISTS environment (
    id UUID PRIMARY KEY,
    profile_name VARCHAR(80) NOT NULL,
    CONSTRAINT uq_environment_profile_name UNIQUE (profile_name),
    temperature_c DOUBLE PRECISION NOT NULL,
    relative_humidity_pct DOUBLE PRECISION NOT NULL CHECK (relative_humidity_pct >= 0 AND relative_humidity_pct <= 100),
    chloride_ppm DOUBLE PRECISION NOT NULL CHECK (chloride_ppm >= 0),
    ph DOUBLE PRECISION NOT NULL CHECK (ph >= 0 AND ph <= 14),
    dissolved_oxygen_mg_l DOUBLE PRECISION NOT NULL CHECK (dissolved_oxygen_mg_l >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_environment_profile_name ON environment (profile_name);
CREATE INDEX IF NOT EXISTS ix_environment_created_at ON environment (created_at);

CREATE TABLE IF NOT EXISTS simulation (
    id UUID PRIMARY KEY,
    material_id UUID NOT NULL REFERENCES materials(id) ON DELETE RESTRICT,
    environment_id UUID NOT NULL REFERENCES environment(id) ON DELETE RESTRICT,
    exposed_area_m2 DOUBLE PRECISION NOT NULL CHECK (exposed_area_m2 > 0),
    exposure_time_hours DOUBLE PRECISION NOT NULL CHECK (exposure_time_hours > 0),
    corrosion_rate_mm_per_year DOUBLE PRECISION NOT NULL CHECK (corrosion_rate_mm_per_year >= 0),
    estimated_lifespan_years DOUBLE PRECISION NOT NULL CHECK (estimated_lifespan_years >= 0),
    accuracy_score DOUBLE PRECISION NULL CHECK (accuracy_score >= 0 AND accuracy_score <= 1),
    risk_classification VARCHAR(40) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_simulation_material_id ON simulation (material_id);
CREATE INDEX IF NOT EXISTS ix_simulation_environment_id ON simulation (environment_id);
CREATE INDEX IF NOT EXISTS ix_simulation_risk_classification ON simulation (risk_classification);

CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY,
    simulation_id UUID NOT NULL REFERENCES simulation(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    report_uri TEXT NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0)
);
CREATE INDEX IF NOT EXISTS ix_reports_simulation_id ON reports (simulation_id);
CREATE INDEX IF NOT EXISTS ix_reports_generated_at ON reports (generated_at);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    auth_method VARCHAR(30) NOT NULL DEFAULT 'local',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY,
    org_name VARCHAR(180) NOT NULL UNIQUE,
    subscription_tier VARCHAR(40) NOT NULL DEFAULT 'free',
    subscription_status VARCHAR(40) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_tenants_org_name ON tenants (org_name);
CREATE INDEX IF NOT EXISTS ix_tenants_subscription_tier ON tenants (subscription_tier);
CREATE INDEX IF NOT EXISTS ix_tenants_subscription_status ON tenants (subscription_status);

CREATE TABLE IF NOT EXISTS tenant_users (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(30) NOT NULL DEFAULT 'viewer',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tenant_user UNIQUE (tenant_id, user_id)
);
CREATE INDEX IF NOT EXISTS ix_tenant_users_tenant_id ON tenant_users (tenant_id);
CREATE INDEX IF NOT EXISTS ix_tenant_users_user_id ON tenant_users (user_id);

CREATE TABLE IF NOT EXISTS tenant_simulations (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    simulation_id UUID NOT NULL REFERENCES simulation(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tenant_simulation UNIQUE (tenant_id, simulation_id)
);
CREATE INDEX IF NOT EXISTS ix_tenant_simulations_tenant_id ON tenant_simulations (tenant_id);
CREATE INDEX IF NOT EXISTS ix_tenant_simulations_simulation_id ON tenant_simulations (simulation_id);

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(120) NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects (user_id);

CREATE TABLE IF NOT EXISTS project_simulations (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    simulation_id UUID NOT NULL REFERENCES simulation(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_project_simulation UNIQUE (project_id, simulation_id)
);
CREATE INDEX IF NOT EXISTS ix_project_simulations_project_id ON project_simulations (project_id);
CREATE INDEX IF NOT EXISTS ix_project_simulations_simulation_id ON project_simulations (simulation_id);

CREATE TABLE IF NOT EXISTS comparison_sets (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(140) NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_comparison_sets_project_id ON comparison_sets (project_id);

CREATE TABLE IF NOT EXISTS comparison_set_simulations (
    id UUID PRIMARY KEY,
    comparison_set_id UUID NOT NULL REFERENCES comparison_sets(id) ON DELETE CASCADE,
    simulation_id UUID NOT NULL REFERENCES simulation(id) ON DELETE CASCADE,
    ordering INTEGER NOT NULL CHECK (ordering >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_comparison_set_simulation UNIQUE (comparison_set_id, simulation_id),
    CONSTRAINT uq_comparison_set_ordering UNIQUE (comparison_set_id, ordering)
);
CREATE INDEX IF NOT EXISTS ix_comparison_set_simulations_set_id ON comparison_set_simulations (comparison_set_id);
CREATE INDEX IF NOT EXISTS ix_comparison_set_simulations_simulation_id ON comparison_set_simulations (simulation_id);

CREATE TABLE IF NOT EXISTS visualizations (
    id UUID PRIMARY KEY,
    simulation_id UUID NOT NULL REFERENCES simulation(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
    mode VARCHAR(20) NOT NULL,
    metadata_json TEXT NOT NULL,
    status VARCHAR(40) NOT NULL,
    overlay_accuracy DOUBLE PRECISION NOT NULL CHECK (overlay_accuracy >= 0 AND overlay_accuracy <= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_visualizations_simulation_id ON visualizations (simulation_id);
CREATE INDEX IF NOT EXISTS ix_visualizations_tenant_id ON visualizations (tenant_id);
CREATE INDEX IF NOT EXISTS ix_visualizations_mode ON visualizations (mode);
CREATE INDEX IF NOT EXISTS ix_visualizations_created_at ON visualizations (created_at);

CREATE TABLE IF NOT EXISTS visualization_exports (
    id UUID PRIMARY KEY,
    visualization_id UUID NOT NULL REFERENCES visualizations(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
    file_type VARCHAR(20) NOT NULL,
    file_uri TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_visualization_exports_visualization_id ON visualization_exports (visualization_id);
CREATE INDEX IF NOT EXISTS ix_visualization_exports_tenant_id ON visualization_exports (tenant_id);
CREATE INDEX IF NOT EXISTS ix_visualization_exports_file_type ON visualization_exports (file_type);
CREATE INDEX IF NOT EXISTS ix_visualization_exports_created_at ON visualization_exports (created_at);

CREATE TABLE IF NOT EXISTS dossiers (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    simulation_id UUID NOT NULL REFERENCES simulation(id) ON DELETE CASCADE,
    format VARCHAR(20) NOT NULL,
    industry_module VARCHAR(80) NOT NULL,
    status VARCHAR(30) NOT NULL,
    content_uri TEXT NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_dossiers_tenant_id ON dossiers (tenant_id);
CREATE INDEX IF NOT EXISTS ix_dossiers_simulation_id ON dossiers (simulation_id);
CREATE INDEX IF NOT EXISTS ix_dossiers_created_at ON dossiers (created_at);

CREATE TABLE IF NOT EXISTS decks (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    export_type VARCHAR(20) NOT NULL,
    status VARCHAR(30) NOT NULL,
    file_uri TEXT NOT NULL,
    generated_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_decks_tenant_id ON decks (tenant_id);
CREATE INDEX IF NOT EXISTS ix_decks_project_id ON decks (project_id);
CREATE INDEX IF NOT EXISTS ix_decks_created_at ON decks (created_at);

CREATE TABLE IF NOT EXISTS consortium_memberships (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    tier VARCHAR(40) NOT NULL,
    status VARCHAR(30) NOT NULL,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT uq_consortium_memberships_tenant UNIQUE (tenant_id)
);
CREATE INDEX IF NOT EXISTS ix_consortium_memberships_tenant_id ON consortium_memberships (tenant_id);
CREATE INDEX IF NOT EXISTS ix_consortium_memberships_tier ON consortium_memberships (tier);
