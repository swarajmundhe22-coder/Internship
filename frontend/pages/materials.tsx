import { FormEvent, useEffect, useState } from "react";

import { FilterBar } from "../components/FilterBar";
import { InputPanel } from "../components/InputPanel";
import { LayoutShell } from "../components/LayoutShell";
import { TableShell } from "../components/TableShell";
import { useApi } from "../hooks/useApi";
import { useUrlQueryState } from "../hooks/useUrlQueryState";
import { Material, MaterialListQueryParams, PaginatedResponse } from "../types/domain";
import { buildQueryString, toDateTimeEnd, toDateTimeStart } from "../utils/query";

export default function MaterialsPage() {
  const { run, loading, error } = useApi();
  const { state, setQuery, isReady } = useUrlQueryState({
    page: "1",
    page_size: "10",
    created_from: "",
    created_to: ""
  });
  const [pageData, setPageData] = useState<PaginatedResponse<Material>>({
    items: [],
    total: 0,
    page: 1,
    page_size: 10
  });
  const [name, setName] = useState("");
  const [alloy, setAlloy] = useState("");
  const [density, setDensity] = useState(7850);
  const [potential, setPotential] = useState(-0.61);

  const page = Number(state.page) || 1;
  const pageSize = Number(state.page_size) || 10;

  async function load() {
    const query: MaterialListQueryParams = {
      page,
      page_size: pageSize,
      created_from: toDateTimeStart(state.created_from),
      created_to: toDateTimeEnd(state.created_to)
    };
    const data = await run<PaginatedResponse<Material>>(`/materials${buildQueryString(query)}`);
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
    await run<Material>("/materials", {
      method: "POST",
      body: JSON.stringify({
        name,
        alloy_group: alloy,
        density_kg_m3: density,
        electrochemical_potential_v: potential
      })
    });
    setName("");
    setAlloy("");
    await load();
  }

  return (
    <LayoutShell title="Materials Management" subtitle="Register and inspect structural materials for corrosion intelligence.">
      <div className="grid gap-4 md:grid-cols-[320px_1fr]">
        <InputPanel title="Create Material" submitLabel="Save Material" onSubmit={submit}>
          <input className="rounded-md border border-slate-300 p-2" placeholder="Material name" value={name} onChange={(e) => setName(e.target.value)} required />
          <input className="rounded-md border border-slate-300 p-2" placeholder="Alloy group" value={alloy} onChange={(e) => setAlloy(e.target.value)} required />
          <input className="rounded-md border border-slate-300 p-2" type="number" step="0.1" value={density} onChange={(e) => setDensity(Number(e.target.value))} required />
          <input className="rounded-md border border-slate-300 p-2" type="number" step="0.01" value={potential} onChange={(e) => setPotential(Number(e.target.value))} required />
        </InputPanel>

        <TableShell
          title="Registered Materials"
          items={pageData.items}
          total={pageData.total}
          page={page}
          pageSize={pageSize}
          loading={loading}
          error={error}
          emptyMessage="No materials found for this page/filter selection."
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
                <li key={item.id} className="rounded-lg border border-slate-200 bg-white p-4">
                  <p className="font-semibold">{item.name}</p>
                  <p className="text-sm text-slate-600">{item.alloy_group}</p>
                  <p className="text-sm text-slate-600">Potential: {item.electrochemical_potential_v} V</p>
                </li>
              ))}
            </ul>
          )}
        </TableShell>
      </div>
    </LayoutShell>
  );
}
