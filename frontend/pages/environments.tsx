import { FormEvent, useEffect, useState } from "react";

import { FilterBar } from "../components/FilterBar";
import { InputPanel } from "../components/InputPanel";
import { LayoutShell } from "../components/LayoutShell";
import { TableShell } from "../components/TableShell";
import { useApi } from "../hooks/useApi";
import { useUrlQueryState } from "../hooks/useUrlQueryState";
import {
  EnvironmentListQueryParams,
  EnvironmentProfile,
  PaginatedResponse
} from "../types/domain";
import { buildQueryString, toDateTimeEnd, toDateTimeStart } from "../utils/query";

export default function EnvironmentsPage() {
  const { run, error, loading } = useApi();
  const { state, setQuery, isReady } = useUrlQueryState({
    page: "1",
    page_size: "10",
    created_from: "",
    created_to: ""
  });
  const [pageData, setPageData] = useState<PaginatedResponse<EnvironmentProfile>>({
    items: [],
    total: 0,
    page: 1,
    page_size: 10
  });
  const [profileName, setProfileName] = useState("");

  const page = Number(state.page) || 1;
  const pageSize = Number(state.page_size) || 10;

  async function load() {
    const query: EnvironmentListQueryParams = {
      page,
      page_size: pageSize,
      created_from: toDateTimeStart(state.created_from),
      created_to: toDateTimeEnd(state.created_to)
    };

    const data = await run<PaginatedResponse<EnvironmentProfile>>(
      `/environment${buildQueryString(query)}`
    );
    setPageData(data);
  }

  useEffect(() => {
    if (!isReady) {
      return;
    }
    void load();
  }, [isReady, state.page, state.page_size, state.created_from, state.created_to]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await run<EnvironmentProfile>("/environment", {
      method: "POST",
      body: JSON.stringify({
        profile_name: profileName,
        temperature_c: 25,
        relative_humidity_pct: 70,
        chloride_ppm: 200,
        ph: 7,
        dissolved_oxygen_mg_l: 7
      })
    });
    setProfileName("");
    await load();
  }

  return (
    <LayoutShell title="Environment Profiles" subtitle="Model operating chemistry and corrosive exposure context.">
      <div className="grid gap-4 md:grid-cols-[320px_1fr]">
        <InputPanel title="Create Environment" submitLabel="Save Profile" onSubmit={submit}>
          <input className="glass-input rounded-md p-2 text-softwhite" placeholder="Profile name" value={profileName} onChange={(e) => setProfileName(e.target.value)} required />
          <p className="text-xs text-softwhite/65">Default starter chemistry values are applied here and can be edited via API later.</p>
        </InputPanel>

        <TableShell
          title="Profiles"
          items={pageData.items}
          total={pageData.total}
          page={page}
          pageSize={pageSize}
          loading={loading}
          error={error}
          emptyMessage="No environments found for this page/filter selection."
          filters={
            <FilterBar
              fields={[
                { key: "created_from", label: "Created From", type: "date" },
                { key: "created_to", label: "Created To", type: "date" }
              ]}
              values={state}
              onChange={(key, value) => setQuery({ [key]: value })}
              onReset={() => setQuery({ created_from: undefined, created_to: undefined })}
            />
          }
          onPageChange={(nextPage) => setQuery({ page: String(nextPage) }, { resetPage: false })}
          onPageSizeChange={(size) =>
            setQuery({ page_size: String(size), page: "1" }, { resetPage: false })
          }
        >
          {(items) => (
            <ul className="grid gap-3">
              {items.map((item) => (
                <li key={item.id} className="rounded-lg border border-lagoon/28 bg-slatewash/35 p-4" data-cinematic-reveal="true">
                  <p className="font-semibold text-softwhite">{item.profile_name}</p>
                  <p className="text-sm text-softwhite/72">
                    RH {item.relative_humidity_pct}% | pH {item.ph} | Cl {item.chloride_ppm} ppm
                  </p>
                </li>
              ))}
            </ul>
          )}
        </TableShell>
      </div>
    </LayoutShell>
  );
}
