import { FilterField, FilterFieldDefinition } from "./FilterField";

type FilterBarProps = {
  fields: FilterFieldDefinition[];
  values: Record<string, string>;
  onChange: (key: string, value: string | undefined) => void;
  onReset: () => void;
};

export function FilterBar({ fields, values, onChange, onReset }: FilterBarProps) {
  return (
    <div className="mb-4 rounded-xl border border-lagoon/30 bg-slatewash/30 p-3 shadow-neon md:p-4" data-cinematic-reveal="true">
      <div className="mb-2 flex items-center justify-between">
        <p className="hud-label text-[11px]">Filter Matrix</p>
      </div>
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
      {fields.map((field) => (
        <FilterField
          key={field.key}
          field={field}
          value={values[field.key] ?? ""}
          onChange={onChange}
        />
      ))}

      <button
        type="button"
        className="holo-btn rounded-md px-3 py-2 text-sm"
        onClick={onReset}
      >
        Reset Filters
      </button>
      </div>
    </div>
  );
}
