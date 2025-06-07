"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { X } from "lucide-react";
import { interestService } from "@/services/api/interest.service";
import { Interest } from "@/types";
import { toast } from "sonner";

interface KeywordFilterProps {
  selectedKeywords: string[];
  onChange: (keywords: string[]) => void;
  onInterestsLoaded?: (interests: Interest[]) => void; // Callback to share loaded interests
}

export function KeywordFilter({
  selectedKeywords,
  onChange,
  onInterestsLoaded,
}: KeywordFilterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [interests, setInterests] = useState<Interest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [dropdownDirection, setDropdownDirection] = useState<"down" | "up">(
    "down"
  );
  const containerRef = useRef<HTMLDivElement>(null);
  const loadingRef = useRef(false); // Prevent concurrent API calls
  // Fetch interests from API
  useEffect(() => {
    const fetchInterests = async () => {
      // Prevent concurrent API calls
      if (loadingRef.current) return;

      try {
        loadingRef.current = true;
        setIsLoading(true);
        const response = await interestService.getAllPublishedInterests();
        setInterests(response);
        // Share loaded interests with parent component
        onInterestsLoaded?.(response);
      } catch {
        toast.error("Không thể tải từ khóa.");
      } finally {
        setIsLoading(false);
        loadingRef.current = false;
      }
    };

    fetchInterests();
  }, [onInterestsLoaded]);
  // Handle clicking outside to close dropdown
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Calculate dropdown direction based on available space
  useEffect(() => {
    if (isOpen && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const spaceBelow = viewportHeight - rect.bottom;
      const spaceAbove = rect.top;

      // If there's more space above and not enough space below, show dropdown upward
      if (spaceBelow < 250 && spaceAbove > spaceBelow) {
        setDropdownDirection("up");
      } else {
        setDropdownDirection("down");
      }
    }
  }, [isOpen]);

  // Add a keyword to selected list
  const addKeyword = (keyword: string) => {
    onChange([...selectedKeywords, keyword]);
  };

  // Remove a keyword from selected list
  const removeKeyword = (keyword: string) => {
    onChange(selectedKeywords.filter((k) => k !== keyword));
  };

  // Find interest object by name
  const getInterestByName = (name: string): Interest | undefined => {
    return interests.find((interest) => interest.name === name);
  };

  // Get available keywords (not already selected)
  const availableInterests = interests.filter(
    (interest) => !selectedKeywords.includes(interest.name)
  );
  return (
    <div
      className="relative min-w-[200px] w-full max-w-[550px]"
      ref={containerRef}
    >
      <div
        className={`flex flex-wrap min-h-10 max-h-24 overflow-y-auto px-3 py-2 border rounded-md ${
          isOpen ? "border-[#6366F1] ring-2 ring-[#6366F1]/20" : "border-input"
        } gap-1 cursor-pointer`}
        onClick={() => setIsOpen(true)}
      >
        {selectedKeywords.length > 0 ? (
          selectedKeywords.map((keyword) => {
            const interest = getInterestByName(keyword);
            const color = interest?.color || "#6366F1";

            return (
              <Badge
                key={keyword}
                className="mb-1 inline-flex"
                style={{
                  backgroundColor: `${color}20`, // 20% opacity
                  color: color,
                  borderColor: `${color}30`, // 30% opacity
                }}
              >
                {keyword}
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-4 w-4 p-0 ml-1 hover:bg-transparent"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeKeyword(keyword);
                  }}
                >
                  <X className="h-3 w-3" />
                </Button>
              </Badge>
            );
          })
        ) : (
          <span className="text-muted-foreground text-sm">Chọn nhãn...</span>
        )}
      </div>{" "}
      {isOpen && (
        <div
          className="absolute z-50 w-full bg-white border rounded-md shadow-lg max-h-60 overflow-auto"
          style={{
            [dropdownDirection === "down" ? "top" : "bottom"]: "100%",
            [dropdownDirection === "down" ? "marginTop" : "marginBottom"]:
              "4px",
            left: 0,
            right: 0,
          }}
        >
          {isLoading ? (
            <div className="px-3 py-2 text-center">Đang tải...</div>
          ) : availableInterests.length > 0 ? (
            availableInterests.map((interest) => (
              <div
                key={interest.id}
                className="px-3 py-2 hover:bg-slate-100 cursor-pointer flex items-center"
                onClick={() => {
                  addKeyword(interest.name);
                  if (availableInterests.length === 1) {
                    setIsOpen(false);
                  }
                }}
              >
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: interest.color }}
                />
                {interest.name}
              </div>
            ))
          ) : (
            <div className="px-3 py-2 text-center text-gray-500">
              Không có từ khóa nào
            </div>
          )}
        </div>
      )}
    </div>
  );
}
