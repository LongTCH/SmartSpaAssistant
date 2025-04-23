"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { X } from "lucide-react";
import { interestService } from "@/services/api/interest.service";
import { Interest } from "@/types";

interface KeywordFilterProps {
  selectedKeywords: string[];
  setSelectedKeywords: (keywords: string[]) => void;
}

export function KeywordFilter({
  selectedKeywords,
  setSelectedKeywords,
}: KeywordFilterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [interests, setInterests] = useState<Interest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);

  // Fetch interests from API
  useEffect(() => {
    const fetchInterests = async () => {
      try {
        setIsLoading(true);
        const response = await interestService.getAllPublishedInterests();
        setInterests(response);
      } catch (error) {
        console.error("Error fetching interests:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchInterests();
  }, []);

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

  // Add a keyword to selected list
  const addKeyword = (keyword: string) => {
    setSelectedKeywords([...selectedKeywords, keyword]);
  };

  // Remove a keyword from selected list
  const removeKeyword = (keyword: string) => {
    setSelectedKeywords(selectedKeywords.filter((k) => k !== keyword));
  };

  // Get available keywords (not already selected)
  const availableKeywords = interests
    .filter(interest => !selectedKeywords.includes(interest.name))
    .map(interest => interest.name);

  return (
    <div className="relative min-w-[250px]" ref={containerRef}>
      <div
        className={`flex flex-wrap min-h-10 px-3 py-2 border rounded-md ${
          isOpen ? "border-[#6366F1] ring-2 ring-[#6366F1]/20" : "border-input"
        } gap-1 cursor-pointer`}
        onClick={() => setIsOpen(true)}
      >
        {selectedKeywords.length > 0 ? (
          selectedKeywords.map((keyword) => (
            <Badge
              key={keyword}
              className="bg-[#6366F1]/10 text-[#6366F1] hover:bg-[#6366F1]/20 border border-[#6366F1]/20"
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
          ))
        ) : (
          <span className="text-muted-foreground text-sm">Chọn từ khóa...</span>
        )}
      </div>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border rounded-md shadow-lg max-h-60 overflow-auto">
          {isLoading ? (
            <div className="px-3 py-2 text-center">Đang tải...</div>
          ) : availableKeywords.length > 0 ? (
            availableKeywords.map((keyword) => (
              <div
                key={keyword}
                className="px-3 py-2 hover:bg-[#6366F1]/10 cursor-pointer"
                onClick={() => {
                  addKeyword(keyword);
                  if (availableKeywords.length === 1) {
                    setIsOpen(false);
                  }
                }}
              >
                {keyword}
              </div>
            ))
          ) : (
            <div className="px-3 py-2 text-center text-gray-500">Không có từ khóa nào</div>
          )}
        </div>
      )}
    </div>
  );
}
