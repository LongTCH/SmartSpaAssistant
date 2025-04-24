"use client";

import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

// Predefined color options
const DEFAULT_COLORS = [
  { name: "Đỏ", value: "#FF5252" },
  { name: "Xanh lá", value: "#4CAF50" },
  { name: "Xanh dương", value: "#2196F3" },
  { name: "Vàng", value: "#FFC107" },
  { name: "Tím", value: "#9C27B0" },
  { name: "Cam", value: "#FF9800" },
  { name: "Hồng", value: "#FF4081" },
  { name: "Xám", value: "#607D8B" },
  { name: "Đỏ đậm", value: "#D32F2F" },
  { name: "Tím hoa cà", value: "#673AB7" },
  { name: "Xanh ngọc", value: "#009688" },
  { name: "Nâu", value: "#795548" },
  { name: "Xanh lơ", value: "#00BCD4" },
  { name: "Xanh lá nhạt", value: "#8BC34A" },
  { name: "Hồng nhạt", value: "#E91E63" },
  { name: "Đen", value: "#212121" },
];

interface ColorPickerProps {
  value: string;
  onChange: (color: string) => void;
  className?: string;
}

export function ColorPicker({ value, onChange, className }: ColorPickerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [customColor, setCustomColor] = useState("");

  // Đảm bảo customColor luôn được đồng bộ với value từ props
  useEffect(() => {
    if (value) {
      setCustomColor(value);
    }
  }, [value]);

  const handleColorSelect = (colorValue: string) => {
    onChange(colorValue);
    setIsOpen(false);
  };

  const handleCustomColorChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newColor = e.target.value;
    setCustomColor(newColor);
  };

  const handleCustomColorBlur = () => {
    if (customColor) {
      onChange(customColor);
    }
  };

  const handleCustomColorKeyDown = (
    e: React.KeyboardEvent<HTMLInputElement>
  ) => {
    if (e.key === "Enter" && customColor) {
      onChange(customColor);
      setIsOpen(false);
    }
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <button
          className={cn(
            "flex items-center gap-2 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background",
            className
          )}
        >
          <div
            className="w-5 h-5 rounded-full border border-gray-300"
            style={{ backgroundColor: value || "#FFFFFF" }}
          />
          <span className="flex-1 text-left">{value || "Chọn màu"}</span>
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-64 p-3">
        <div className="space-y-3">
          <div className="space-y-1.5">
            <label className="text-xs font-medium">Màu có sẵn</label>
            <div className="grid grid-cols-4 gap-2">
              {DEFAULT_COLORS.map((color) => (
                <div
                  key={color.value}
                  className={`w-full aspect-square rounded cursor-pointer flex items-center justify-center border-2 hover:opacity-90 ${
                    value === color.value
                      ? "border-gray-800"
                      : "border-transparent"
                  }`}
                  style={{ backgroundColor: color.value }}
                  onClick={() => handleColorSelect(color.value)}
                  title={color.name}
                >
                  {value === color.value && (
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-4 w-4 text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium">Màu tùy chọn</label>
            <div className="flex items-center gap-2">
              <Input
                type="text"
                placeholder="Nhập mã màu (vd: #FF5252)"
                value={customColor}
                onChange={handleCustomColorChange}
                onBlur={handleCustomColorBlur}
                onKeyDown={handleCustomColorKeyDown}
              />
              {customColor && (
                <div
                  className="w-8 h-8 rounded-full flex-shrink-0 border border-gray-300"
                  style={{ backgroundColor: customColor }}
                />
              )}
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
