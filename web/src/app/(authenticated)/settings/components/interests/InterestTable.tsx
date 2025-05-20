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
import { Interest } from "@/types";

interface InterestTableProps {
  ITEMS_PER_PAGE: number;
  interests: Interest[];
  isLoading: boolean;
  status: string;
  selectedInterestIds: Set<string>;
  allCurrentPageSelected: boolean;
  handleSelectInterest: (id: string, checked: boolean) => void;
  handleSelectAllOnPage: (checked: boolean) => void;
  handleEditInterest: (id: string) => void;
  handleSingleInterestDelete: (id: string) => void;
}
export function InterestTable({
  ITEMS_PER_PAGE,
  interests,
  isLoading,
  status,
  selectedInterestIds,
  allCurrentPageSelected,
  handleSelectInterest,
  handleSelectAllOnPage,
  handleEditInterest,
  handleSingleInterestDelete,
}: InterestTableProps) {
  return (
    <div className="border rounded-md">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12 border-r">
              <Checkbox
                checked={allCurrentPageSelected}
                onCheckedChange={handleSelectAllOnPage}
                disabled={interests.length === 0}
              />
            </TableHead>
            <TableHead className="text-[#6366F1] border-r">Nhãn</TableHead>
            <TableHead className="text-[#6366F1] border-r">Các từ khóa</TableHead>
            <TableHead className="text-[#6366F1] border-r w-20">
              Màu sắc
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
          ) : interests.length > 0 ? (
            interests.map((interest) => (
              <TableRow key={interest.id}>
                <TableCell className="border-r">
                  <Checkbox
                    checked={selectedInterestIds.has(interest.id)}
                    onCheckedChange={(checked) =>
                      handleSelectInterest(interest.id, checked === true)
                    }
                  />
                </TableCell>
                <TableCell className="border-r w-1/4">
                  {interest.name}
                </TableCell>
                <TableCell className="border-r">
                  {interest.related_terms}
                </TableCell>
                <TableCell className="border-r">
                  {interest.color ? (
                    <div className="flex items-center">
                      <div
                        className="w-4 h-4 rounded-full mr-2"
                        style={{ backgroundColor: interest.color }}
                      ></div>
                      <span className="text-xs">{interest.color}</span>
                    </div>
                  ) : (
                    <span className="text-xs text-gray-400">Chưa đặt màu</span>
                  )}
                </TableCell>
                <TableCell className="border-r">
                  <div
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      interest.status === "published"
                        ? "bg-green-100 text-green-800"
                        : "bg-yellow-100 text-yellow-800"
                    }`}
                  >
                    {interest.status === "published" ? "Xuất bản" : "Bản nháp"}
                  </div>
                </TableCell>

                <TableCell className="text-right">
                  <div className="flex justify-end space-x-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      title="Chỉnh sửa"
                      onClick={() => handleEditInterest(interest.id)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      title="Xóa"
                      onClick={() => handleSingleInterestDelete(interest.id)}
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                Không có nhãn nào{" "}
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
