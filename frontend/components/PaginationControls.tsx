type PaginationControlsProps = {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
};

export function PaginationControls({
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange
}: PaginationControlsProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const start = Math.max(1, page - 2);
  const end = Math.min(totalPages, start + 4);
  const pageNumbers = Array.from({ length: end - start + 1 }, (_, idx) => start + idx);

  return (
    <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-softwhite/90">
      <button
        type="button"
        className="holo-btn rounded-md px-3 py-1 disabled:opacity-40"
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
      >
        Previous
      </button>

      {pageNumbers.map((pageNumber) => (
        <button
          key={pageNumber}
          type="button"
          className={`rounded-md px-3 py-1 ${
            pageNumber === page ? "animate-hud-pulse border border-lagoon/70 bg-lagoon/20 text-softwhite" : "holo-btn"
          }`}
          onClick={() => onPageChange(pageNumber)}
        >
          {pageNumber}
        </button>
      ))}

      <button
        type="button"
        className="holo-btn rounded-md px-3 py-1 disabled:opacity-40"
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
      >
        Next
      </button>

      <label className="ml-auto flex items-center gap-2 text-softwhite/85">
        Page size
        <select
          className="glass-input rounded-md px-2 py-1"
          value={pageSize}
          onChange={(event) => onPageSizeChange(Number(event.target.value))}
        >
          {[10, 25, 50, 100].map((size) => (
            <option key={size} value={size}>
              {size}
            </option>
          ))}
        </select>
      </label>

      <span className="hud-label text-[10px] text-softwhite/70">Total: {total}</span>
    </div>
  );
}
