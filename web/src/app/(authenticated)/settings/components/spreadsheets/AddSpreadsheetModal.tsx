"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface AddSpreadsheetModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddSpreadsheetModal({
  open,
  onOpenChange,
}: AddSpreadsheetModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-center">
            Thêm bảng tính
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-6 py-4 overflow-y-auto pr-1">
          <div className="space-y-2">
            <label className="text-sm font-medium">Trạng thái:</label>
            <Select defaultValue="published">
              <SelectTrigger>
                <SelectValue placeholder="Xuất bản" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="published">Xuất bản</SelectItem>
                <SelectItem value="draft">Bản nháp</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Tên:</label>
            <Input placeholder="BỘ SẢN PHẨM" />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Mô tả:</label>
            <Textarea
              className="min-h-[100px]"
              placeholder="Dữ liệu về các bộ sản phẩm của thẩm mỹ viện
Các trường:
product_name: Tên bộ sản phẩm
sku_code: Mã SKU
price: Giá bán
user_manual: Hướng dẫn sử dụng"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Dữ liệu</label>
            <div className="border rounded-md overflow-hidden max-h-[300px] overflow-y-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12 border-r">#</TableHead>
                    <TableHead className="border-r">product_name</TableHead>
                    <TableHead className="border-r">sku_code</TableHead>
                    <TableHead className="border-r">price</TableHead>
                    <TableHead>user_manual</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="border-r">1</TableCell>
                    <TableCell className="border-r">
                      Bộ N3 - Trị nám tàn nhang
                    </TableCell>
                    <TableCell className="border-r">N3</TableCell>
                    <TableCell className="border-r">1,000,000 Đ</TableCell>
                    <TableCell>
                      Giúp nghiên nát, phá vỡ sắc tố melanin, ức chế sự sản sinh
                      melanin quá mức, giúp da căng, trắng, mịn.
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="border-r">2</TableCell>
                    <TableCell className="border-r">
                      Bộ NM - Trị mụn trứng cá
                    </TableCell>
                    <TableCell className="border-r">NM</TableCell>
                    <TableCell className="border-r">600,000 Đ</TableCell>
                    <TableCell></TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="border-r">3</TableCell>
                    <TableCell className="border-r">
                      Bộ C02 - Com đo gạo tiên
                    </TableCell>
                    <TableCell className="border-r">C02</TableCell>
                    <TableCell className="border-r">300,000 Đ</TableCell>
                    <TableCell></TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          </div>
        </div>
        <DialogFooter className="flex-shrink-0">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button className="bg-[#6366F1] hover:bg-[#4F46E5] text-white">
            Lưu
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
