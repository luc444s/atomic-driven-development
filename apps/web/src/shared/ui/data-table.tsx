import { ReactNode } from "react";

import { cn } from "./cn";

export type DataTableColumn<Row> = {
  key: string;
  header: string;
  className?: string;
  render: (row: Row) => ReactNode;
};

type DataTableProps<Row> = {
  columns: DataTableColumn<Row>[];
  rows: Row[];
  rowKey: (row: Row) => string;
  emptyMessage: string;
};

export function DataTable<Row>({ columns, rows, rowKey, emptyMessage }: DataTableProps<Row>) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950/70">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-800 text-sm text-slate-200">
          <thead className="bg-slate-900/80 text-left text-xs uppercase tracking-wide text-slate-400">
            <tr>
              {columns.map((column) => (
                <th key={column.key} className={cn("px-4 py-3 font-semibold", column.className)}>
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {rows.length > 0 ? (
              rows.map((row) => (
                <tr key={rowKey(row)} className="align-top">
                  {columns.map((column) => (
                    <td key={column.key} className={cn("px-4 py-3", column.className)}>
                      {column.render(row)}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length} className="px-4 py-8 text-center text-slate-500">
                  {emptyMessage}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
