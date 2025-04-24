"use client";

import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface CustomerPaginationProps {
  page: number;
  totalPages: number;
  total: number;
  limit: number;
  onPageChange: (page: number) => void;
}

export function CustomerPagination({
  page,
  totalPages,
  total,
  limit,
  onPageChange,
}: CustomerPaginationProps) {
  return (
    <div className="flex justify-between items-center mt-6">
      <div className="text-sm text-gray-500">
        {total > 0
          ? `Hiển thị ${(page - 1) * limit + 1} - ${Math.min(
              page * limit,
              total
            )} trong số ${total} khách hàng`
          : "Không có khách hàng nào"}
      </div>

      <div className="flex items-center space-x-2">
        {/* Nút First Page */}
        <Button
          variant="outline"
          size="icon"
          className="h-10 w-10"
          onClick={() => onPageChange(1)}
          disabled={page === 1}
        >
          <ChevronLeft className="h-4 w-4 mr-1" />
          <ChevronLeft className="h-4 w-4 -ml-3" />
        </Button>

        {/* Nút Previous */}
        <Button
          variant="outline"
          size="icon"
          className="h-10 w-10"
          onClick={() => onPageChange(page - 1)}
          disabled={page === 1}
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
          } else if (page <= 3) {
            // If near the start, show 1,2,3,4,5
            pageNum = i + 1;
          } else if (page >= totalPages - 2) {
            // If near the end, show last 5 pages
            pageNum = totalPages - 4 + i;
          } else {
            // Otherwise, show current page and 2 on each side
            pageNum = page - 2 + i;
          }

          return (
            <Button
              key={pageNum}
              variant={pageNum === page ? "default" : "outline"}
              className={
                pageNum === page
                  ? "bg-[#6366F1] text-white h-10 w-10"
                  : "h-10 w-10"
              }
              onClick={() => onPageChange(pageNum)}
            >
              {pageNum}
            </Button>
          );
        })}

        {/* Nút Next */}
        <Button
          variant="outline"
          size="icon"
          className="h-10 w-10"
          onClick={() => onPageChange(page + 1)}
          disabled={page === totalPages}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>

        {/* Nút Last Page */}
        <Button
          variant="outline"
          size="icon"
          className="h-10 w-10"
          onClick={() => onPageChange(totalPages)}
          disabled={page === totalPages}
        >
          <ChevronRight className="h-4 w-4 mr-1" />
          <ChevronRight className="h-4 w-4 -ml-3" />
        </Button>
      </div>
    </div>
  );
}
