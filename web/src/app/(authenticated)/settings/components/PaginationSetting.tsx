"use client";

import { Button } from "@/components/ui/button";






import {
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

interface PaginationSettingProps {
  totalItems: number;
  currentPage: number;
  ITEMS_PER_PAGE: number;
  totalPages: number;
  handlePageChange: (page: number) => void;
}

export function PaginationSetting({
  totalItems,
  currentPage,
  ITEMS_PER_PAGE,
  totalPages,
  handlePageChange,
}: PaginationSettingProps) {
  return (
    <>
      {totalPages > 0 && (
        <div className="flex justify-between items-center mt-6">
          <div className="text-sm text-gray-500">
            {totalItems > 0
              ? `Hiển thị ${
                  (currentPage - 1) * ITEMS_PER_PAGE + 1
                } - ${Math.min(
                  currentPage * ITEMS_PER_PAGE,
                  totalItems
                )} trong số ${totalItems} hàng`
              : "Không có dữ liệu"}
          </div>

          <div className="flex items-center space-x-2">
            {/* Nút First Page */}
            <Button
              variant="outline"
              size="icon"
              className="h-10 w-10"
              onClick={() => handlePageChange(1)}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              <ChevronLeft className="h-4 w-4 -ml-3" />
            </Button>

            <Button
              variant="outline"
              size="icon"
              className="h-10 w-10"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>

            {/* Generate page buttons */}
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              // Show at most 5 page buttons
              let pageNum;
              if (totalPages <= 5) {
                // If 5 or fewer pages, show all
                pageNum = i + 1;
              } else if (currentPage <= 3) {
                // If near the start, show 1,2,3,4,5
                pageNum = i + 1;
              } else if (currentPage >= totalPages - 2) {
                // If near the end, show last 5 pages
                pageNum = totalPages - 4 + i;
              } else {
                // Otherwise, show current page and 2 on each side
                pageNum = currentPage - 2 + i;
              }

              return (
                <Button
                  key={pageNum}
                  variant={pageNum === currentPage ? "default" : "outline"}
                  className={
                    pageNum === currentPage
                      ? "bg-[#6366F1] text-white h-10 w-10"
                      : "h-10 w-10"
                  }
                  onClick={() => handlePageChange(pageNum)}
                >
                  {pageNum}
                </Button>
              );
            })}

            <Button
              variant="outline"
              size="icon"
              className="h-10 w-10"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>

            {/* Nút Last Page */}
            <Button
              variant="outline"
              size="icon"
              className="h-10 w-10"
              onClick={() => handlePageChange(totalPages)}
              disabled={currentPage === totalPages}
            >
              <ChevronRight className="h-4 w-4 mr-1" />
              <ChevronRight className="h-4 w-4 -ml-3" />
            </Button>
          </div>
        </div>
      )}
    </>
  );
}
