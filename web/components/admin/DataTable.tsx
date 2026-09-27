import React from 'react';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    ChevronLeft,
    ChevronRight,
    Search,
    Edit,
    Trash2,
    Plus,
    MoreHorizontal
} from "lucide-react";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface Column {
    key: string;
    label: string;
    render?: (value: any, row: any) => React.ReactNode;
}

interface DataTableProps {
    columns: Column[];
    data: any[];
    total: number;
    page: number;
    pageSize: number;
    onPageChange: (page: number) => void;
    onSearch?: (query: string) => void;
    onAdd?: () => void;
    onEdit?: (item: any) => void;
    onDelete?: (item: any) => void;
    isLoading?: boolean;
    title?: string;
    searchPlaceholder?: string;
}

export function DataTable({
    columns,
    data,
    total,
    page,
    pageSize,
    onPageChange,
    onSearch,
    onAdd,
    onEdit,
    onDelete,
    isLoading,
    title,
    searchPlaceholder = "Search..."
}: DataTableProps) {
    const totalPages = Math.ceil(total / pageSize);

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                {title && <h2 className="text-2xl font-bold tracking-tight">{title}</h2>}
                <div className="flex items-center gap-2">
                    {onSearch && (
                        <div className="relative w-64">
                            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder={searchPlaceholder}
                                className="pl-8"
                                onChange={(e) => onSearch(e.target.value)}
                            />
                        </div>
                    )}
                    {onAdd && (
                        <Button onClick={onAdd}>
                            <Plus className="mr-2 h-4 w-4" /> Add New
                        </Button>
                    )}
                </div>
            </div>

            <div className="rounded-md border">
                <Table>
                    <TableHeader>
                        <TableRow>
                            {columns.map((col) => (
                                <TableHead key={col.key}>{col.label}</TableHead>
                            ))}
                            {(onEdit || onDelete) && <TableHead className="w-[100px]">Actions</TableHead>}
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading ? (
                            <TableRow>
                                <TableCell colSpan={columns.length + (onEdit || onDelete ? 1 : 0)} className="h-24 text-center">
                                    Loading...
                                </TableCell>
                            </TableRow>
                        ) : data.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={columns.length + (onEdit || onDelete ? 1 : 0)} className="h-24 text-center">
                                    No results found.
                                </TableCell>
                            </TableRow>
                        ) : (
                            data.map((row, i) => (
                                <TableRow key={row.id || i}>
                                    {columns.map((col) => (
                                        <TableCell key={`${row.id}-${col.key}`}>
                                            {col.render ? col.render(row[col.key], row) : row[col.key]}
                                        </TableCell>
                                    ))}
                                    {(onEdit || onDelete) && (
                                        <TableCell>
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" className="h-8 w-8 p-0">
                                                        <span className="sr-only">Open menu</span>
                                                        <MoreHorizontal className="h-4 w-4" />
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    <DropdownMenuLabel>Actions</DropdownMenuLabel>
                                                    {onEdit && (
                                                        <DropdownMenuItem onClick={() => onEdit(row)}>
                                                            <Edit className="mr-2 h-4 w-4" /> Edit
                                                        </DropdownMenuItem>
                                                    )}
                                                    {onDelete && (
                                                        <DropdownMenuItem onClick={() => onDelete(row)} className="text-red-600">
                                                            <Trash2 className="mr-2 h-4 w-4" /> Delete
                                                        </DropdownMenuItem>
                                                    )}
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </TableCell>
                                    )}
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </div>

            <div className="flex items-center justify-end space-x-2 py-4">
                <div className="text-sm text-muted-foreground">
                    Page {page} of {totalPages || 1}
                </div>
                <div className="space-x-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onPageChange(page - 1)}
                        disabled={page <= 1}
                    >
                        <ChevronLeft className="h-4 w-4" />
                        Previous
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onPageChange(page + 1)}
                        disabled={page >= totalPages}
                    >
                        Next
                        <ChevronRight className="h-4 w-4" />
                    </Button>
                </div>
            </div>
        </div>
    );
}
