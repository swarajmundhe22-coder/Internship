import { useEffect, useState } from "react";

import { useDebouncedValue } from "../hooks/useDebouncedValue";

type FilterOption = {
  label: string;
  value: string;
};

export type FilterFieldDefinition = {
  key: string;
  label: string;
  type: "text" | "select" | "date";
  placeholder?: string;
  options?: FilterOption[];
  debounceMs?: number;
};

type FilterFieldProps = {
  field: FilterFieldDefinition;
  value: string;
  onChange: (key: string, value: string | undefined) => void;
};

export function FilterField({ field, value, onChange }: FilterFieldProps) {
  const [draft, setDraft] = useState(value);
  const debounced = useDebouncedValue(draft, field.debounceMs ?? 300);

  useEffect(() => {
    setDraft(value);
  }, [value, field.key]);

  useEffect(() => {
    if (field.type !== "text") {
      return;
    }
    onChange(field.key, debounced || undefined);
  }, [debounced, field.key, field.type]);

  if (field.type === "select") {
    return (
      <label className="grid gap-1 text-xs text-softwhite/90">
        {field.label}
        <select
          className="glass-input rounded-md p-2 text-sm"
          value={value}
          onChange={(event) => onChange(field.key, event.target.value || undefined)}
        >
          <option value="">All</option>
          {(field.options ?? []).map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
    );
  }

  if (field.type === "date") {
    return (
      <label className="grid gap-1 text-xs text-softwhite/90">
        {field.label}
        <input
          type="date"
          className="glass-input rounded-md p-2 text-sm"
          value={value}
          onChange={(event) => onChange(field.key, event.target.value || undefined)}
        />
      </label>
    );
  }

  return (
    <label className="grid gap-1 text-xs text-softwhite/90">
      {field.label}
      <input
        type="text"
        className="glass-input rounded-md p-2 text-sm"
        value={draft}
        placeholder={field.placeholder}
        onChange={(event) => setDraft(event.target.value)}
      />
    </label>
  );
}
