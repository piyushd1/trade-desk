"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card } from "@/components/ui/card";
import { LoadingSpinner } from "./LoadingSpinner";
import type { TableColumn } from "@/lib/types";

interface DataTableProps<T> {
  /** Array of data to display */
  data: T[];
  /** Column definitions */
  columns: TableColumn<T>[];
  /** Unique key for each row */
  keyField: keyof T;
  /** Loading state */
  loading?: boolean;
  /** Empty state message */
  emptyMessage?: string;
  /** Whether to show card wrapper */
  showCard?: boolean;
  /** Additional table className */
  className?: string;
  /** Row click handler */
  onRowClick?: (item: T) => void;
}

/**
 * Generic data table component
 * 
 * @example
 * ```tsx
 * const columns: TableColumn<User>[] = [
 *   { key: 'name', header: 'Name' },
 *   { key: 'email', header: 'Email' },
 *   { 
 *     key: 'status', 
 *     header: 'Status',
 *     accessor: (user) => <Badge>{user.status}</Badge>
 *   }
 * ];
 * 
 * <DataTable data={users} columns={columns} keyField="id" />
 * ```
 */
export function DataTable<T extends Record<string, any>>({
  data,
  columns,
  keyField,
  loading = false,
  emptyMessage = "No data available",
  showCard = true,
  className,
  onRowClick,
}: DataTableProps<T>) {
  if (loading) {
    return <LoadingSpinner center text="Loading data..." />;
  }

  const tableContent = (
    <Table className={className}>
      <TableHeader>
        <TableRow>
          {columns.map((column) => (
            <TableHead key={String(column.key)} className={column.className}>
              {column.header}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.length === 0 ? (
          <TableRow>
            <TableCell 
              colSpan={columns.length} 
              className="text-center text-muted-foreground"
            >
              {emptyMessage}
            </TableCell>
          </TableRow>
        ) : (
          data.map((item) => (
            <TableRow
              key={String(item[keyField])}
              onClick={() => onRowClick?.(item)}
              className={onRowClick ? "cursor-pointer hover:bg-muted/50" : undefined}
            >
              {columns.map((column) => (
                <TableCell key={String(column.key)} className={column.className}>
                  {column.accessor 
                    ? column.accessor(item) 
                    : item[column.key as keyof T]
                  }
                </TableCell>
              ))}
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  );

  if (showCard) {
    return <Card>{tableContent}</Card>;
  }

  return tableContent;
}
