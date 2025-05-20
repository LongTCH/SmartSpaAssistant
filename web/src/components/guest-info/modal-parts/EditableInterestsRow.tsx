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
        backgroundColor: `${interest.color}20`,
        color: interest.color,
        borderColor: `${interest.color}30`,
      };
    }
    return {};
  };

  return (
    <div className="flex flex-col space-y-1">
      <div className="flex items-center justify-between">
        <label className="font-medium text-sm">{label}:</label>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-gray-500"
          onClick={() =>
            isEditable ? onReset(fieldName) : onToggleEdit(fieldName)
          }
        >
          {isEditable ? (
            <RotateCcw className="h-3.5 w-3.5" />
          ) : (
            <Edit className="h-3.5 w-3.5" />
          )}
        </Button>
      </div>
      <div className="flex-1 relative" ref={interestsContainerRef}>
        {isEditable ? (
          <>
            <div
              className="flex flex-wrap gap-1 p-2 border rounded-md min-h-[36px] bg-white cursor-text text-sm"
              onClick={() => setIsInterestsDropdownOpen(true)}
            >
              {selectedInterestNames.map((name) => (
                <Badge
                  key={name}
                  className="flex items-center gap-1 text-xs"
                  style={getInterestColorStyle(name)}
                >
                  {name}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeInterest(name);
                    }}
                    className="ml-0.5 rounded-full hover:bg-gray-300 p-0.5"
                  >
                    <X className="h-2.5 w-2.5" />
                  </button>
                </Badge>
              ))}
              {selectedInterestNames.length === 0 &&
                !isInterestsDropdownOpen && (
                  <span className="text-gray-400 text-sm">Chọn sở thích</span>
                )}
            </div>
            {isInterestsDropdownOpen && (
              <div className="absolute z-10 mt-1 w-full bg-white border rounded-md shadow-lg max-h-52 overflow-y-auto text-sm">
                <div className="p-1.5">
                  <div className="relative">
                    <Input
                      type="text"
                      placeholder="Tìm sở thích..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pr-7 text-sm"
                    />
                    <Search className="absolute right-1.5 top-1/2 transform -translate-y-1/2 h-3.5 w-3.5 text-gray-400" />
                  </div>
                </div>
                {isInterestsLoading ? (
                  <div className="p-1.5 text-center text-xs">Đang tải...</div>
                ) : filteredInterests.length > 0 ? (
                  filteredInterests.map((interest) => (
                    <div
                      key={interest.id}
                      className="p-1.5 hover:bg-gray-100 cursor-pointer text-sm"
                      onClick={() => {
                        addInterest(interest.name);
                        setSearchTerm("");
                      }}
                    >
                      {interest.name}
                    </div>
                  ))
                ) : (
                  <div className="p-1.5 text-center text-gray-500 text-xs">
                    Không tìm thấy sở thích nào.
                  </div>
                )}
              </div>
            )}
          </>
        ) : (
          <div className="flex flex-wrap gap-1 p-2 border rounded-md min-h-[36px] bg-gray-50 text-sm">
            {selectedInterestNames.length > 0 ? (
              selectedInterestNames.map((name) => (
                <Badge
                  key={name}
                  style={getInterestColorStyle(name)}
                  className="text-xs"
                >
                  {name}
                </Badge>
              ))
            ) : (
              <span className="text-gray-400 text-sm">Chưa có thông tin</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
