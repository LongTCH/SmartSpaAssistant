"use client";

import { useState } from "react";
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
  Upload,
  Plus,
  Trash2,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { AddSpreadsheetModal } from "./AddSpreadsheetModal";

export function SpreadsheetsTab() {
  const [showSpreadsheetModal, setShowSpreadsheetModal] = useState(false);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">BẢNG TÍNH</h1>

      <div className="flex items-center space-x-4 mb-6">
        <Button variant="outline" className="space-x-2">
          <Download className="h-4 w-4" />
          <span>Export file</span>
        </Button>
        <Button variant="outline" className="space-x-2">
          <Upload className="h-4 w-4" />
          <span>Upload file</span>
        </Button>
        <Button
          className="bg-[#6366F1] hover:bg-[#4F46E5] text-white space-x-2"
          onClick={() => setShowSpreadsheetModal(true)}
        >
          <Plus className="h-4 w-4" />
          <span>Thêm bảng tính mới</span>
        </Button>
      </div>

      <div className="border rounded-md">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12 border-r">
                <Checkbox />
              </TableHead>
              <TableHead className="text-[#6366F1] border-r">
                Tên bảng tính
              </TableHead>
              <TableHead className="text-right text-[#6366F1]">
                Thao tác
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {["BỘ SẢN PHẨM", "BẢNG GIÁ DỊCH VỤ"].map((sheet, index) => (
              <TableRow key={index}>
                <TableCell className="border-r">
                  <Checkbox />
                </TableCell>
                <TableCell className="border-r">{sheet}</TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end space-x-2">
                    <Button variant="ghost" size="icon">
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon">
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="flex justify-center items-center mt-6 space-x-2">
        <Button variant="outline" size="icon" className="h-10 w-10">
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <Button className="bg-[#6366F1] text-white h-10 w-10">1</Button>
        <Button variant="outline" className="h-10 w-10">
          2
        </Button>
        <Button variant="outline" size="icon" className="h-10 w-10">
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      <AddSpreadsheetModal
        open={showSpreadsheetModal}
        onOpenChange={setShowSpreadsheetModal}
      />
    </div>
  );
}
