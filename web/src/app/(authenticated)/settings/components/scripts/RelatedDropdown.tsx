"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { X } from "lucide-react";

interface Item {
  id: string;
  name: string;
}

interface RelatedDropdownProps<T extends Item> {
  label: string;
  items: T[];
  selectedIds: string[];
  onToggleItem: (id: string) => void;
  onRemoveItem: (id: string) => void;
  badgeClassName?: string;
  placeholder?: string;
  emptyMessage?: string;
}

export function RelatedDropdown<T extends Item>({
  label,
  items,
  selectedIds,
  onToggleItem,
  onRemoveItem,
  badgeClassName = "bg-blue-100 text-blue-800 border-blue-200",
  placeholder = "Chọn mục",
  emptyMessage = "Không có mục nào khả dụng",
}: RelatedDropdownProps<T>) {
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const getItemById = (id: string): T | undefined => {
    return items.find((item) => item.id === id);
  };

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">{label}:</label>
      <div className="relative" ref={dropdownRef}>
        <div
          className="flex flex-wrap min-h-10 max-h-24 overflow-y-auto px-3 py-2 border rounded-md gap-1 cursor-pointer"
          onClick={() => setShowDropdown(true)}
        >
          {selectedIds && selectedIds.length > 0 ? (
            selectedIds.map((id) => {
              const item = getItemById(id);
              return item ? (
                <Badge
                  key={id}
                  className={`mb-1 inline-flex ${badgeClassName}`}
                >
                  {item.name}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-4 w-4 p-0 ml-1 hover:bg-transparent"
                    onClick={(e) => {
                      e.stopPropagation();
                      onRemoveItem(id);
                    }}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </Badge>
              ) : null;
            })
          ) : (
            <span className="text-sm text-gray-500">{placeholder}</span>
          )}
        </div>

        {showDropdown && (
          <div
            className="absolute z-50 w-full mt-1 bg-white border rounded-md shadow-lg max-h-60 overflow-auto"
            style={{ bottom: "auto" }}
          >
            <div className="p-2">
              {items.filter((item) => !selectedIds.includes(item.id)).length >
              0 ? (
                items
                  .filter((item) => !selectedIds.includes(item.id))
                  .map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center px-2 py-2 hover:bg-gray-100 rounded-md cursor-pointer"
                      onClick={() => {
                        onToggleItem(item.id);
                        if (
                          items.filter((i) => !selectedIds.includes(i.id))
                            .length === 1
                        ) {
                          setShowDropdown(false);
                        }
                      }}
                    >
                      <Checkbox
                        id={`item-${item.id}`}
                        checked={selectedIds.includes(item.id)}
                        className="mr-2"
                      />
                      <label
                        htmlFor={`item-${item.id}`}
                        className="flex-1 cursor-pointer text-sm"
                      >
                        {item.name}
                      </label>
                    </div>
                  ))
              ) : (
                <div className="px-2 py-2 text-center text-gray-500 text-sm">
                  {emptyMessage}
                </div>
              )}
            </div>
            <div className="p-2 border-t">
              <Button
                variant="ghost"
                className="w-full text-center text-sm py-1"
                onClick={() => setShowDropdown(false)}
              >
                Đóng
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
