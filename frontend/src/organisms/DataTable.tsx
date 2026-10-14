import type { ReactNode } from 'react'
import { Card } from '../atoms/Card'

export interface Column<T> {
  header: string
  cell: (row: T) => ReactNode
  className?: string
}

export function DataTable<T>({
  columns,
  rows,
  keyOf,
  empty = 'Sin registros',
  onRowClick,
}: {
  columns: Column<T>[]
  rows: T[]
  keyOf: (row: T) => string
  empty?: string
  onRowClick?: (row: T) => void
}) {
  if (rows.length === 0) {
    return (
      <Card className="p-8 text-center">
        <p className="text-body-md text-on-surface-variant">{empty}</p>
      </Card>
    )
  }
  return (
    <Card className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-surface-container-low">
            <tr>
              {columns.map((c) => (
                <th
                  key={c.header}
                  className={`border-b border-outline-variant/60 px-space-lg py-space-md text-label-md font-semibold tracking-wide text-on-surface-variant uppercase ${c.className ?? ''}`}
                >
                  {c.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={keyOf(row)}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={`border-b border-outline-variant/40 last:border-b-0 transition-colors ${
                  onRowClick ? 'cursor-pointer hover:bg-surface-container-low' : ''
                }`}
              >
                {columns.map((c) => (
                  <td
                    key={c.header}
                    className={`px-space-lg py-space-md text-body-md text-on-surface ${c.className ?? ''}`}
                  >
                    {c.cell(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}
