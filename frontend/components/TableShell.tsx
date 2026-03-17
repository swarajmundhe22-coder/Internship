import { ReactNode } from "react";

import { PaginationControls } from "./PaginationControls";

type TableShellProps<T> = {
  title: string;
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  loading: boolean;
  error?: string | null;
  emptyMessage: string;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  filters?: ReactNode;
  children: (items: T[]) => ReactNode;
};

export function TableShell<T>({
  title,
  items,
  total,
  page,
  pageSize,
  loading,
  error,
  emptyMessage,
  onPageChange,
  onPageSizeChange,
  filters,
  children
}: TableShellProps<T>) {
  return (
    <section className="mt-4 panel table-shell p-6" data-cinematic-reveal="true">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-2">
        <h2 className="text-xl font-semibold text-softwhite">{title}</h2>
        <p className="hud-label text-[10px]">Enterprise Query Surface</p>
      </div>
      {filters}

      {loading && <p className="text-sm text-softwhite/70">Loading...</p>}
      {error && <p className="text-sm text-red-300">{error}</p>}
      {!loading && !error && items.length === 0 && (
        <p className="text-sm text-softwhite/70">{emptyMessage}</p>
      )}

      {!loading && !error && items.length > 0 && children(items)}

      <PaginationControls
        page={page}
        pageSize={pageSize}
        total={total}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
      />
    </section>
  );
}
