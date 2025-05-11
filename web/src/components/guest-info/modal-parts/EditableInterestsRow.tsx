"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Edit, RotateCcw, X, Search } from "lucide-react"; // Plus removed as we are not adding new from here
import type { Interest } from "@/types/interest";

interface EditableInterestsRowProps {
  label: string;
  isEditable: boolean;
  fieldName: "interests";
  onToggleEdit: (fieldName: "interests") => void;
  onReset: (fieldName: "interests") => void;
  selectedInterestNames: string[];
  availableInterests: Interest[];
  addInterest: (interestName: string) => void;
  removeInterest: (interestName: string) => void;
  isInterestsLoading: boolean;
  isInterestsDropdownOpen: boolean;
  setIsInterestsDropdownOpen: (isOpen: boolean) => void;
  interestsContainerRef: React.RefObject<HTMLDivElement | null>;
}

export function EditableInterestsRow({
  label,
  isEditable,
  fieldName,
  onToggleEdit,
  onReset,
  selectedInterestNames,
  availableInterests,
  addInterest,
  removeInterest,
  isInterestsLoading,
  isInterestsDropdownOpen,
  setIsInterestsDropdownOpen,
  interestsContainerRef,
}: EditableInterestsRowProps) {
  const [searchTerm, setSearchTerm] = useState("");

  const filteredInterests = availableInterests.filter(
    (interest) =>
      interest.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
      !selectedInterestNames.includes(interest.name)
  );

  const getInterestColorStyle = (interestName: string) => {
    const interest = availableInterests.find((i) => i.name === interestName);
    if (interest && interest.color) {
      return {
        backgroundColor: `${interest.color}20`, // 20% opacity
        color: interest.color,
        borderColor: `${interest.color}30`, // 30% opacity
      };
    }
    return {}; // Fallback to default Badge styling if no color found
  };

  return (
    <div className="flex items-start justify-between">
      <div className="w-[120px] font-medium pt-2">{label}:</div>
      <div className="flex-1 flex items-start">
        <div className="flex-1 relative" ref={interestsContainerRef}>
          {isEditable ? (
            <>
              <div
                className="flex flex-wrap gap-2 p-2 border rounded-md min-h-[40px] bg-white cursor-text"
                onClick={() => setIsInterestsDropdownOpen(true)}
              >
                {selectedInterestNames.map((name) => (
                  <Badge
                    key={name}
                    // variant="secondary" // Remove or keep if you want to mix styles
                    className="flex items-center gap-1"
                    style={getInterestColorStyle(name)}
                  >
                    {name}
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        removeInterest(name);
                      }}
                      className="ml-1 rounded-full hover:bg-gray-300 p-0.5"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
                {selectedInterestNames.length === 0 &&
                  !isInterestsDropdownOpen && (
                    <span className="text-gray-400">Chọn sở thích</span>
                  )}
              </div>
              {isInterestsDropdownOpen && (
                <div className="absolute z-10 mt-1 w-full bg-white border rounded-md shadow-lg max-h-60 overflow-y-auto">
                  <div className="p-2">
                    <div className="relative">
                      <Input
                        type="text"
                        placeholder="Tìm sở thích..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pr-8"
                      />
                      <Search className="absolute right-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    </div>
                  </div>
                  {isInterestsLoading ? (
                    <div className="p-2 text-center">Đang tải...</div>
                  ) : filteredInterests.length > 0 ? (
                    filteredInterests.map((interest) => (
                      <div
                        key={interest.id}
                        className="p-2 hover:bg-gray-100 cursor-pointer"
                        onClick={() => {
                          addInterest(interest.name);
                          setSearchTerm("");
                        }}
                      >
                        {interest.name}
                      </div>
                    ))
                  ) : (
                    <div className="p-2 text-center text-gray-500">
                      Không tìm thấy sở thích nào.
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="flex flex-wrap gap-2 p-2 border rounded-md min-h-[40px] bg-gray-50">
              {selectedInterestNames.length > 0 ? (
                selectedInterestNames.map((name) => (
                  <Badge
                    key={name}
                    // variant="secondary" // Remove or keep if you want to mix styles
                    style={getInterestColorStyle(name)}
                  >
                    {name}
                  </Badge>
                ))
              ) : (
                <span className="text-gray-400">Chưa có thông tin</span>
              )}
            </div>
          )}
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="ml-2 h-8 w-8 text-gray-500 self-start mt-1"
          onClick={() =>
            isEditable ? onReset(fieldName) : onToggleEdit(fieldName)
          }
        >
          {isEditable ? (
            <RotateCcw className="h-4 w-4" />
          ) : (
            <Edit className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  );
}
