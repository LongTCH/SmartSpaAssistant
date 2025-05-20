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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Plus, Trash2 } from "lucide-react";
import { TemplateEditor } from "../TemplateEditor";

interface Parameter {
  id: string;
  name: string;
  type: string;
  description: string;
}

interface ConfigStepProps {
  parameters: Parameter[];
  addParameter: () => void;
  updateParameter: (id: string, field: keyof Parameter, value: string) => void;
  deleteParameter: (id: string) => void;
  content: string;
  setContent: (content: string) => void;
}

export function ConfigStep({
  parameters,
  addParameter,
  updateParameter,
  deleteParameter,
  content,
  setContent,
}: ConfigStepProps) {
  return (
    <div className="space-y-6 p-4">
      <div className="space-y-2">
        <div className="border rounded-md overflow-auto max-h-[300px]">
          <Table>
            <TableHeader className="sticky top-0 bg-white z-10">
              <TableRow>
                <TableHead className="w-1/4">Tham số</TableHead>
                <TableHead className="w-1/4">Kiểu dữ liệu</TableHead>
                <TableHead className="w-1/2">Mô tả</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {parameters.map((param) => (
                <TableRow key={param.id}>
                  <TableCell className="p-2">
                    <Input
                      value={param.name}
                      onChange={(e) =>
                        updateParameter(param.id, "name", e.target.value)
                      }
                      placeholder="customer_name"
                    />
                  </TableCell>
                  <TableCell className="p-2">
                    <Select
                      value={param.type}
                      onValueChange={(value) =>
                        updateParameter(param.id, "type", value)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="String">String</SelectItem>
                        <SelectItem value="Integer">Integer</SelectItem>
                        <SelectItem value="Numeric">Numeric</SelectItem>
                        <SelectItem value="DateTime">DateTime</SelectItem>
                        <SelectItem value="Boolean">Boolean</SelectItem>
                      </SelectContent>
                    </Select>
                  </TableCell>
                  <TableCell className="p-2">
                    <Textarea
                      value={param.description}
                      onChange={(e) =>
                        updateParameter(param.id, "description", e.target.value)
                      }
                      placeholder="Mô tả tham số"
                      className="min-h-[38px] max-h-[150px] resize-y w-full"
                    />
                  </TableCell>
                  <TableCell className="p-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteParameter(param.id)}
                      className="h-8 w-8 p-0"
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {parameters.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={4}
                    className="text-center py-4 text-gray-500"
                  >
                    Chưa có tham số nào. Bấm &quot;Thêm hàng&quot; để thêm tham số.
                  </TableCell>
                </TableRow>
              )}
              <TableRow>
                <TableCell colSpan={4} className="p-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={addParameter}
                    className="flex items-center gap-1 w-full justify-center"
                  >
                    <Plus className="h-4 w-4" />
                    <span>Thêm hàng</span>
                  </Button>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
        <p className="text-xs text-gray-500 italic">
          Lưu ý: Tên tham số nên đặt đơn giản, không chứa khoảng trắng hay ký tự
          đặc biệt. Nếu gồm nhiều từ, hãy dùng chữ thường và nối với nhau bằng
          dấu gạch dưới (ví dụ: <code>ten_khach_hang</code>,{" "}
          <code>ma_san_pham</code>).
        </p>
      </div>
      <div className="space-y-2">
        <label className="text-sm font-medium">Nội dung:</label>
        <TemplateEditor
          value={content}
          onChange={setContent}
          parameters={parameters}
          className="min-h-[200px]"
        />
        <p className="text-xs text-gray-500 italic">
          Sử dụng cú pháp{" "}
          <code className="bg-gray-100 px-1 rounded">
            {"{{ tên_tham_số }}"}
          </code>{" "}
          để chèn giá trị động vào nội dung thông báo.
        </p>
      </div>
    </div>
  );
}
