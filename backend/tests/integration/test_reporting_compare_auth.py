import pytest
from httpx import AsyncClient
from uuid import uuid4


async def _create_material_environment_simulation(
    api_client: AsyncClient,
    headers: dict[str, str],
    *,
    material_name: str,
    profile_name: str,
    corrosion_rate: float,
    lifespan: float,
    risk: str,
):
    material_response = await api_client.post(
        "/api/v1/materials",
        json={
            "name": material_name,
            "alloy_group": "Ferrous",
            "density_kg_m3": 7850.0,
            "electrochemical_potential_v": -0.61,
        },
        headers=headers,
    )
    environment_response = await api_client.post(
        "/api/v1/environment",
        json={
            "profile_name": profile_name,
            "temperature_c": 25.0,
            "relative_humidity_pct": 70.0,
            "chloride_ppm": 200.0,
            "ph": 6.8,
            "dissolved_oxygen_mg_l": 6.5,
        },
        headers=headers,
    )

    material = material_response.json()
    environment = environment_response.json()

    simulation_response = await api_client.post(
        "/api/v1/simulation",
        json={
            "material_id": material["id"],
            "environment_id": environment["id"],
            "exposed_area_m2": 10.0,
            "exposure_time_hours": 500.0,
            "corrosion_rate_mm_per_year": corrosion_rate,
            "estimated_lifespan_years": lifespan,
            "risk_classification": risk,
            "version": 1,
        },
        headers=headers,
    )
    return material, environment, simulation_response.json()


@pytest.mark.asyncio
async def test_generate_report_endpoint(api_client: AsyncClient) -> None:
    headers = await _register_and_get_headers(api_client, "report-generate")
    _, _, simulation = await _create_material_environment_simulation(
        api_client,
        headers,
        material_name="Report Test Material",
        profile_name="Report Test Environment",
        corrosion_rate=0.12,
        lifespan=8.0,
        risk="high",
    )

    response = await api_client.post(
        "/api/v1/reports/generate",
        json={"simulation_id": simulation["id"]},
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["simulation_id"] == simulation["id"]
    assert payload["metrics"]["risk_classification"] == "high"
    assert "recommendation_summary" in payload


@pytest.mark.asyncio
async def test_compare_simulations_endpoint(api_client: AsyncClient) -> None:
    headers = await _register_and_get_headers(api_client, "compare")
    _, _, left = await _create_material_environment_simulation(
        api_client,
        headers,
        material_name="Compare Left",
        profile_name="Compare Left Env",
        corrosion_rate=0.05,
        lifespan=20.0,
        risk="moderate",
    )
    _, _, right = await _create_material_environment_simulation(
        api_client,
        headers,
        material_name="Compare Right",
        profile_name="Compare Right Env",
        corrosion_rate=0.15,
        lifespan=7.0,
        risk="high",
    )

    response = await api_client.post(
        "/api/v1/compare/simulations",
        json={
            "left_simulation_id": left["id"],
            "right_simulation_id": right["id"],
        },
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["corrosion_rate_delta_mm_per_year"] > 0
    assert "risk_transition" in payload


@pytest.mark.asyncio
async def test_auth_and_projects_scaffold(api_client: AsyncClient) -> None:
    email = f"engineer-{uuid4().hex}@example.com"

    register_response = await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123"},
    )
    if register_response.status_code == 200:
        token = register_response.json()["access_token"]
    else:
        assert register_response.status_code == 409
        fallback_login = await api_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "StrongPass123"},
        )
        assert fallback_login.status_code == 200
        token = fallback_login.json()["access_token"]

    login_response = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPass123"},
    )
    assert login_response.status_code == 200

    headers = {"Authorization": f"Bearer {token}"}

    create_project = await api_client.post(
        "/api/v1/projects",
        json={"name": "Pipeline Rehabilitation Program"},
        headers=headers,
    )
    assert create_project.status_code == 200
    project = create_project.json()

    list_projects = await api_client.get("/api/v1/projects", headers=headers)
    assert list_projects.status_code == 200
    assert len(list_projects.json()) == 1

    _, _, simulation = await _create_material_environment_simulation(
        api_client,
        headers,
        material_name="Save Sim Material",
        profile_name="Save Sim Environment",
        corrosion_rate=0.08,
        lifespan=14.0,
        risk="moderate",
    )

    save_response = await api_client.post(
        f"/api/v1/projects/{project['id']}/simulations",
        json={"simulation_id": simulation["id"]},
        headers=headers,
    )
    assert save_response.status_code == 200
    assert save_response.json()["status"] == "saved"


@pytest.mark.asyncio
async def test_project_detail_includes_associated_simulations(api_client: AsyncClient) -> None:
    email = f"project-detail-{uuid4().hex}@example.com"
    register_response = await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123"},
    )
    assert register_response.status_code == 200
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_project = await api_client.post(
        "/api/v1/projects",
        json={"name": "Detail Validation Project"},
        headers=headers,
    )
    assert create_project.status_code == 200
    project = create_project.json()

    material, environment, simulation = await _create_material_environment_simulation(
        api_client,
        headers,
        material_name="Project Detail Material",
        profile_name="Project Detail Environment",
        corrosion_rate=0.09,
        lifespan=11.5,
        risk="moderate",
    )

    attach_response = await api_client.post(
        f"/api/v1/projects/{project['id']}/simulations/{simulation['id']}",
        headers=headers,
    )
    assert attach_response.status_code == 200
    assert attach_response.json()["status"] == "saved"

    detail_response = await api_client.get(f"/api/v1/projects/{project['id']}", headers=headers)
    assert detail_response.status_code == 200
    payload = detail_response.json()

    assert payload["id"] == project["id"]
    assert payload["name"] == "Detail Validation Project"
    assert payload["simulations"]["total"] == 1
    assert payload["simulations"]["page"] == 1
    assert payload["simulations"]["page_size"] == 25
    assert len(payload["simulations"]["items"]) == 1

    summary = payload["simulations"]["items"][0]
    assert summary["simulation_id"] == simulation["id"]
    assert summary["material"] == material["name"]
    assert summary["environment"] == environment["profile_name"]
    assert summary["risk_level"] == simulation["risk_classification"]
    assert summary["lifespan_years"] == simulation["estimated_lifespan_years"]


@pytest.mark.asyncio
async def test_project_detail_not_found_for_non_owner(api_client: AsyncClient) -> None:
    owner_email = f"owner-{uuid4().hex}@example.com"
    owner_register = await api_client.post(
        "/api/v1/auth/register",
        json={"email": owner_email, "password": "StrongPass123"},
    )
    assert owner_register.status_code == 200
    owner_headers = {"Authorization": f"Bearer {owner_register.json()['access_token']}"}

    create_project = await api_client.post(
        "/api/v1/projects",
        json={"name": "Owner Project"},
        headers=owner_headers,
    )
    assert create_project.status_code == 200
    project_id = create_project.json()["id"]

    viewer_email = f"viewer-{uuid4().hex}@example.com"
    viewer_register = await api_client.post(
        "/api/v1/auth/register",
        json={"email": viewer_email, "password": "StrongPass123"},
    )
    assert viewer_register.status_code == 200
    viewer_headers = {"Authorization": f"Bearer {viewer_register.json()['access_token']}"}

    detail_response = await api_client.get(f"/api/v1/projects/{project_id}", headers=viewer_headers)
    assert detail_response.status_code == 404


@pytest.mark.asyncio
async def test_project_detail_supports_filtering_and_pagination(api_client: AsyncClient) -> None:
    email = f"project-page-filter-{uuid4().hex}@example.com"
    register_response = await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123"},
    )
    assert register_response.status_code == 200
    headers = {"Authorization": f"Bearer {register_response.json()['access_token']}"}

    create_project = await api_client.post(
        "/api/v1/projects",
        json={"name": "Project Query Spec Validation"},
        headers=headers,
    )
    assert create_project.status_code == 200
    project = create_project.json()

    _, _, moderate_simulation = await _create_material_environment_simulation(
        api_client,
        headers,
        material_name="Project Filter Material Moderate",
        profile_name="Project Filter Environment Moderate",
        corrosion_rate=0.06,
        lifespan=13.0,
        risk="moderate",
    )
    _, _, high_simulation = await _create_material_environment_simulation(
        api_client,
        headers,
        material_name="Project Filter Material High",
        profile_name="Project Filter Environment High",
        corrosion_rate=0.14,
        lifespan=6.0,
        risk="high",
    )

    attach_moderate = await api_client.post(
        f"/api/v1/projects/{project['id']}/simulations/{moderate_simulation['id']}",
        headers=headers,
    )
    assert attach_moderate.status_code == 200

    attach_high = await api_client.post(
        f"/api/v1/projects/{project['id']}/simulations/{high_simulation['id']}",
        headers=headers,
    )
    assert attach_high.status_code == 200

    page_response = await api_client.get(
        f"/api/v1/projects/{project['id']}?page=1&page_size=1",
        headers=headers,
    )
    assert page_response.status_code == 200
    page_payload = page_response.json()
    assert page_payload["simulations"]["total"] == 2
    assert page_payload["simulations"]["page"] == 1
    assert page_payload["simulations"]["page_size"] == 1
    assert len(page_payload["simulations"]["items"]) == 1

    risk_filtered = await api_client.get(
        f"/api/v1/projects/{project['id']}?risk_level=high",
        headers=headers,
    )
    assert risk_filtered.status_code == 200
    risk_payload = risk_filtered.json()
    assert risk_payload["simulations"]["total"] == 1
    assert len(risk_payload["simulations"]["items"]) == 1
    assert risk_payload["simulations"]["items"][0]["simulation_id"] == high_simulation["id"]
    assert risk_payload["simulations"]["items"][0]["risk_level"] == "high"


@pytest.mark.asyncio
async def test_project_reports_support_filters_and_pagination(api_client: AsyncClient) -> None:
    email = f"project-reports-{uuid4().hex}@example.com"
    register_response = await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123"},
    )
    assert register_response.status_code == 200
    headers = {"Authorization": f"Bearer {register_response.json()['access_token']}"}

    create_project = await api_client.post(
        "/api/v1/projects",
        json={"name": "Project Reports Workspace"},
        headers=headers,
    )
    assert create_project.status_code == 200
    project = create_project.json()

    _, _, moderate_simulation = await _create_material_environment_simulation(
        api_client,
        headers,
        material_name="Report Hub Material Moderate",
        profile_name="Report Hub Env Moderate",
        corrosion_rate=0.05,
        lifespan=15.0,
        risk="moderate",
    )
    _, _, high_simulation = await _create_material_environment_simulation(
        api_client,
        headers,
        material_name="Report Hub Material High",
        profile_name="Report Hub Env High",
        corrosion_rate=0.2,
        lifespan=4.5,
        risk="high",
    )

    for simulation_id in (moderate_simulation["id"], high_simulation["id"]):
        attach = await api_client.post(
            f"/api/v1/projects/{project['id']}/simulations/{simulation_id}",
            headers=headers,
        )
        assert attach.status_code == 200

    moderate_report = await api_client.post(
        "/api/v1/reports",
        json={
            "simulation_id": moderate_simulation["id"],
            "report_uri": "https://reports.local/moderate.html",
            "status": "generated",
            "version": 1,
        },
        headers=headers,
    )
    assert moderate_report.status_code == 201

    high_report = await api_client.post(
        "/api/v1/reports",
        json={
            "simulation_id": high_simulation["id"],
            "report_uri": "https://reports.local/high.html",
            "status": "generated",
            "version": 1,
        },
        headers=headers,
    )
    assert high_report.status_code == 201

    page_response = await api_client.get(
        f"/api/v1/projects/{project['id']}/reports?page=1&page_size=1",
        headers=headers,
    )
    assert page_response.status_code == 200
    page_payload = page_response.json()
    assert page_payload["total"] == 2
    assert page_payload["page"] == 1
    assert page_payload["page_size"] == 1
    assert len(page_payload["items"]) == 1

    risk_response = await api_client.get(
        f"/api/v1/projects/{project['id']}/reports?risk_level=high",
        headers=headers,
    )
    assert risk_response.status_code == 200
    risk_payload = risk_response.json()
    assert risk_payload["total"] == 1
    assert risk_payload["items"][0]["simulation_id"] == high_simulation["id"]
    assert risk_payload["items"][0]["risk_level"] == "high"

    future_response = await api_client.get(
        f"/api/v1/projects/{project['id']}/reports?created_from=2999-01-01T00:00:00Z",
        headers=headers,
    )
    assert future_response.status_code == 200
    future_payload = future_response.json()
    assert future_payload["total"] == 0
    assert len(future_payload["items"]) == 0

    assert moderate_report.json()["id"] != high_report.json()["id"]


@pytest.mark.asyncio
async def test_project_reports_enforce_project_ownership(api_client: AsyncClient) -> None:
    owner_email = f"project-reports-owner-{uuid4().hex}@example.com"
    owner_register = await api_client.post(
        "/api/v1/auth/register",
        json={"email": owner_email, "password": "StrongPass123"},
    )
    assert owner_register.status_code == 200
    owner_headers = {"Authorization": f"Bearer {owner_register.json()['access_token']}"}

    create_project = await api_client.post(
        "/api/v1/projects",
        json={"name": "Owner Only Reports"},
        headers=owner_headers,
    )
    assert create_project.status_code == 200
    project_id = create_project.json()["id"]

    viewer_email = f"project-reports-viewer-{uuid4().hex}@example.com"
    viewer_register = await api_client.post(
        "/api/v1/auth/register",
        json={"email": viewer_email, "password": "StrongPass123"},
    )
    assert viewer_register.status_code == 200
    viewer_headers = {"Authorization": f"Bearer {viewer_register.json()['access_token']}"}

    unauthorized = await api_client.get(
        f"/api/v1/projects/{project_id}/reports",
        headers=viewer_headers,
    )
    assert unauthorized.status_code == 404


async def _register_and_get_headers(api_client: AsyncClient, prefix: str) -> dict[str, str]:
    register_response = await api_client.post(
        "/api/v1/auth/register",
        json={"email": f"{prefix}-{uuid4().hex}@example.com", "password": "StrongPass123"},
    )
    assert register_response.status_code == 200
    token = register_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_comparison_set_crud_and_payload(api_client: AsyncClient) -> None:
    headers = await _register_and_get_headers(api_client, "comparison-set-owner")

    create_project = await api_client.post(
        "/api/v1/projects",
        json={"name": "Comparison Set Project"},
        headers=headers,
    )
    assert create_project.status_code == 200
    project = create_project.json()

    _, _, sim_a = await _create_material_environment_simulation(
        api_client,
        headers,
        material_name="Comp Set Material A",
        profile_name="Comp Set Env A",
        corrosion_rate=0.03,
        lifespan=18.0,
        risk="low",
    )
    _, _, sim_b = await _create_material_environment_simulation(
        api_client,
        headers,
        material_name="Comp Set Material B",
        profile_name="Comp Set Env B",
        corrosion_rate=0.08,
        lifespan=11.0,
        risk="moderate",
    )
    _, _, sim_c = await _create_material_environment_simulation(
        api_client,
        headers,
        material_name="Comp Set Material C",
        profile_name="Comp Set Env C",
        corrosion_rate=0.15,
        lifespan=6.0,
        risk="high",
    )

    for simulation_id in (sim_a["id"], sim_b["id"], sim_c["id"]):
        attach_response = await api_client.post(
            f"/api/v1/projects/{project['id']}/simulations/{simulation_id}",
            headers=headers,
        )
        assert attach_response.status_code == 200

    create_set = await api_client.post(
        f"/api/v1/projects/{project['id']}/comparison-sets",
        json={
            "name": "Bridge Corridor Scenarios",
            "simulation_ids": [sim_a["id"], sim_b["id"]],
        },
        headers=headers,
    )
    assert create_set.status_code == 200
    created_payload = create_set.json()
    comparison_set_id = created_payload["id"]
    assert created_payload["project_id"] == project["id"]
    assert created_payload["simulation_ids"] == [sim_a["id"], sim_b["id"]]
    assert len(created_payload["comparisons"]) == 1
    assert created_payload["comparisons"][0]["left_simulation_id"] == sim_a["id"]
    assert created_payload["comparisons"][0]["right_simulation_id"] == sim_b["id"]
    assert "->" in created_payload["comparisons"][0]["risk_transition"]

    list_sets = await api_client.get(f"/api/v1/projects/{project['id']}/comparison-sets", headers=headers)
    assert list_sets.status_code == 200
    list_payload = list_sets.json()
    assert len(list_payload) == 1
    assert list_payload[0]["id"] == comparison_set_id
    assert list_payload[0]["simulation_count"] == 2

    updated_set = await api_client.patch(
        f"/api/v1/comparison-sets/{comparison_set_id}",
        json={
            "name": "Bridge Corridor Updated",
            "simulation_ids": [sim_a["id"], sim_b["id"], sim_c["id"]],
        },
        headers=headers,
    )
    assert updated_set.status_code == 200
    updated_payload = updated_set.json()
    assert updated_payload["name"] == "Bridge Corridor Updated"
    assert updated_payload["simulation_ids"] == [sim_a["id"], sim_b["id"], sim_c["id"]]
    assert len(updated_payload["comparisons"]) == 2

    get_set = await api_client.get(f"/api/v1/comparison-sets/{comparison_set_id}", headers=headers)
    assert get_set.status_code == 200
    get_payload = get_set.json()
    assert get_payload["id"] == comparison_set_id
    assert len(get_payload["comparisons"]) == 2

    delete_set = await api_client.delete(f"/api/v1/comparison-sets/{comparison_set_id}", headers=headers)
    assert delete_set.status_code == 204

    get_deleted = await api_client.get(f"/api/v1/comparison-sets/{comparison_set_id}", headers=headers)
    assert get_deleted.status_code == 404


@pytest.mark.asyncio
async def test_comparison_set_validation_and_cross_project_rejection(api_client: AsyncClient) -> None:
    owner_headers = await _register_and_get_headers(api_client, "comparison-set-validation-owner")

    project_one = await api_client.post(
        "/api/v1/projects",
        json={"name": "Comparison Validation One"},
        headers=owner_headers,
    )
    assert project_one.status_code == 200
    project_two = await api_client.post(
        "/api/v1/projects",
        json={"name": "Comparison Validation Two"},
        headers=owner_headers,
    )
    assert project_two.status_code == 200

    _, _, sim_one = await _create_material_environment_simulation(
        api_client,
        owner_headers,
        material_name="Cross Project Material 1",
        profile_name="Cross Project Env 1",
        corrosion_rate=0.04,
        lifespan=16.0,
        risk="low",
    )
    _, _, sim_two = await _create_material_environment_simulation(
        api_client,
        owner_headers,
        material_name="Cross Project Material 2",
        profile_name="Cross Project Env 2",
        corrosion_rate=0.09,
        lifespan=12.0,
        risk="moderate",
    )
    _, _, sim_other_project = await _create_material_environment_simulation(
        api_client,
        owner_headers,
        material_name="Cross Project Material 3",
        profile_name="Cross Project Env 3",
        corrosion_rate=0.18,
        lifespan=5.0,
        risk="high",
    )

    attach_one = await api_client.post(
        f"/api/v1/projects/{project_one.json()['id']}/simulations/{sim_one['id']}",
        headers=owner_headers,
    )
    assert attach_one.status_code == 200
    attach_two = await api_client.post(
        f"/api/v1/projects/{project_one.json()['id']}/simulations/{sim_two['id']}",
        headers=owner_headers,
    )
    assert attach_two.status_code == 200
    attach_other = await api_client.post(
        f"/api/v1/projects/{project_two.json()['id']}/simulations/{sim_other_project['id']}",
        headers=owner_headers,
    )
    assert attach_other.status_code == 200

    invalid_simulation = await api_client.post(
        f"/api/v1/projects/{project_one.json()['id']}/comparison-sets",
        json={
            "name": "Invalid Simulation UUIDs",
            "simulation_ids": [sim_one["id"], str(uuid4())],
        },
        headers=owner_headers,
    )
    assert invalid_simulation.status_code == 400

    cross_project = await api_client.post(
        f"/api/v1/projects/{project_one.json()['id']}/comparison-sets",
        json={
            "name": "Cross Project Rejection",
            "simulation_ids": [sim_one["id"], sim_other_project["id"]],
        },
        headers=owner_headers,
    )
    assert cross_project.status_code == 400


@pytest.mark.asyncio
async def test_comparison_set_permission_enforcement(api_client: AsyncClient) -> None:
    owner_headers = await _register_and_get_headers(api_client, "comparison-set-perm-owner")
    outsider_headers = await _register_and_get_headers(api_client, "comparison-set-perm-outsider")

    project_response = await api_client.post(
        "/api/v1/projects",
        json={"name": "Comparison Permissions Project"},
        headers=owner_headers,
    )
    assert project_response.status_code == 200
    project_id = project_response.json()["id"]

    _, _, sim_one = await _create_material_environment_simulation(
        api_client,
        owner_headers,
        material_name="Perm Material 1",
        profile_name="Perm Env 1",
        corrosion_rate=0.06,
        lifespan=10.0,
        risk="moderate",
    )
    _, _, sim_two = await _create_material_environment_simulation(
        api_client,
        owner_headers,
        material_name="Perm Material 2",
        profile_name="Perm Env 2",
        corrosion_rate=0.11,
        lifespan=7.5,
        risk="high",
    )

    for simulation_id in (sim_one["id"], sim_two["id"]):
        attach_response = await api_client.post(
            f"/api/v1/projects/{project_id}/simulations/{simulation_id}",
            headers=owner_headers,
        )
        assert attach_response.status_code == 200

    created_set = await api_client.post(
        f"/api/v1/projects/{project_id}/comparison-sets",
        json={"name": "Perm Set", "simulation_ids": [sim_one["id"], sim_two["id"]]},
        headers=owner_headers,
    )
    assert created_set.status_code == 200
    comparison_set_id = created_set.json()["id"]

    unauthorized_list = await api_client.get(
        f"/api/v1/projects/{project_id}/comparison-sets",
        headers=outsider_headers,
    )
    assert unauthorized_list.status_code == 404

    unauthorized_create = await api_client.post(
        f"/api/v1/projects/{project_id}/comparison-sets",
        json={"name": "Forbidden", "simulation_ids": [sim_one["id"], sim_two["id"]]},
        headers=outsider_headers,
    )
    assert unauthorized_create.status_code == 404

    unauthorized_get = await api_client.get(
        f"/api/v1/comparison-sets/{comparison_set_id}",
        headers=outsider_headers,
    )
    assert unauthorized_get.status_code == 404

    unauthorized_delete = await api_client.delete(
        f"/api/v1/comparison-sets/{comparison_set_id}",
        headers=outsider_headers,
    )
    assert unauthorized_delete.status_code == 404
