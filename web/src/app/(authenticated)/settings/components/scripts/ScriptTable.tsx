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
  Pencil,
  Trash2,
} from "lucide-react";
import { Script } from "@/types";


interface ScriptTableProps {
    ITEMS_PER_PAGE: number;
  scripts: Script[];
  isLoading: boolean;
  status: string;
  selectedScriptIds: Set<string>;
  allCurrentPageSelected: boolean;
  handleSelectScript: (id: string, checked: boolean) => void;
  handleSelectAllOnPage: (checked: boolean) => void;
  handleSingleScriptDelete: (id: string) => void;
  handleEditScript: (id: string) => void;
}

export function ScriptTable({
    ITEMS_PER_PAGE,
  scripts,
  isLoading,
  status,
  selectedScriptIds,
  allCurrentPageSelected,
  handleSelectScript,
  handleSelectAllOnPage,
  handleSingleScriptDelete,
  handleEditScript,
}: ScriptTableProps) {
  return (
    <div className="border rounded-md">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12 border-r">
              <Checkbox
                checked={allCurrentPageSelected}
                onCheckedChange={handleSelectAllOnPage}
                disabled={scripts.length === 0}
              />
            </TableHead>
            <TableHead className="text-[#6366F1] border-r">
              Tên kịch bản
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
          ) : scripts.length > 0 ? (
            scripts.map((script) => (
              <TableRow key={script.id}>
                <TableCell className="border-r">
                  <Checkbox
                    checked={selectedScriptIds.has(script.id)}
                    onCheckedChange={(checked) =>
                      handleSelectScript(script.id, checked === true)
                    }
                  />
                </TableCell>
                <TableCell className="border-r">{script.name}</TableCell>
                <TableCell className="border-r">
                  <div
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      script.status === "published"
                        ? "bg-green-100 text-green-800"
                        : "bg-yellow-100 text-yellow-800"
                    }`}
                  >
                    {script.status === "published" ? "Xuất bản" : "Bản nháp"}
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end space-x-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      title="Chỉnh sửa"
                      onClick={() => handleEditScript(script.id)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      title="Xóa"
                      onClick={() => handleSingleScriptDelete(script.id)}
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
                Không có kịch bản nào{" "}
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
