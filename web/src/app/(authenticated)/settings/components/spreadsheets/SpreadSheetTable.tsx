"use client";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";




import {
  Download,
  Pencil,
  Trash2,
  Eye,
} from "lucide-react";
interface SpreadSheetTableProps {
  ITEMS_PER_PAGE: number;
  sheets: any[];
  isLoading: boolean;
  status: string;
  selectedSheetIds: Set<string>;
  allCurrentPageSelected: boolean;
  handleSelectSheet: (id: string, checked: boolean) => void;
  handleSelectAllOnPage: (checked: boolean) => void;
  handlePreviewSheet: (sheet: any) => void;
  handleDownloadSheet: (id: string, name: string) => void;
  handleEditSheet: (sheet: any) => void;
  handleSingleSheetDelete: (id: string) => void;
}

export function SpreadSheetTable({
  ITEMS_PER_PAGE,
  sheets,
  isLoading,
  status,
  selectedSheetIds,
  allCurrentPageSelected,
  handleSelectSheet,
  handleSelectAllOnPage,
  handlePreviewSheet,
  handleDownloadSheet,
  handleEditSheet,
  handleSingleSheetDelete,
}: SpreadSheetTableProps) {
  return (
    <div className="border rounded-md">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12 border-r">
              <Checkbox
                checked={allCurrentPageSelected}
                onCheckedChange={handleSelectAllOnPage}
                disabled={sheets.length === 0}
              />
            </TableHead>
            <TableHead className="text-[#6366F1] border-r">
              Tên bảng tính
            </TableHead>
            <TableHead className="text-[#6366F1] border-r w-24">
              Trạng thái
            </TableHead>
            <TableHead className="text-right text-[#6366F1] w-36">
              Thao tác
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            // Loading state
            Array(ITEMS_PER_PAGE)
              .fill(0)
              .map((_, index) => (
                <TableRow key={`loading-${index}`}>
                  <TableCell className="border-r">
                    <div className="w-4 h-4 bg-gray-200 animate-pulse rounded"></div>
                  </TableCell>
                  <TableCell className="border-r">
                    <div className="w-full h-4 bg-gray-200 animate-pulse rounded"></div>
                  </TableCell>
                  <TableCell className="border-r">
                    <div className="w-24 h-4 bg-gray-200 animate-pulse rounded"></div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end space-x-2">
                      <div className="w-8 h-8 bg-gray-200 animate-pulse rounded"></div>
                      <div className="w-8 h-8 bg-gray-200 animate-pulse rounded"></div>
                    </div>
                  </TableCell>
                </TableRow>
              ))
          ) : sheets.length > 0 ? (
            sheets.map((sheet) => (
              <TableRow key={sheet.id}>
                <TableCell className="border-r">
                  <Checkbox
                    checked={selectedSheetIds.has(sheet.id)}
                    onCheckedChange={(checked) =>
                      handleSelectSheet(sheet.id, checked === true)
                    }
                  />
                </TableCell>
                <TableCell className="border-r">{sheet.name}</TableCell>
                <TableCell className="border-r">
                  <div
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      sheet.status === "published"
                        ? "bg-green-100 text-green-800"
                        : "bg-yellow-100 text-yellow-800"
                    }`}
                  >
                    {sheet.status === "published" ? "Xuất bản" : "Bản nháp"}
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end space-x-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      title="Xem trước"
                      onClick={() => handlePreviewSheet(sheet)}
                    >
                      <Eye className="h-4 w-4 text-green-500" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      title="Tải về"
                      onClick={() => handleDownloadSheet(sheet.id, sheet.name)}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      title="Chỉnh sửa"
                      onClick={() => handleEditSheet(sheet)}
                    >
                      <Pencil className="h-4 w-4 text-blue-500" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      title="Xóa"
                      onClick={() => handleSingleSheetDelete(sheet.id)}
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-8 text-gray-500">
                Không có bảng tính nào{" "}
                {status !== "all" &&
                  `có trạng thái "${
                    status === "published" ? "Xuất bản" : "Bản nháp"
                  }"`}
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
