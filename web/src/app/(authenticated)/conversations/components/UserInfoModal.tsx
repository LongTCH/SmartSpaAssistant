"use client";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Conversation, GuestInfoUpdate, Interest } from "@/types";
import { Edit, RotateCcw, X } from "lucide-react";
import { useEffect, useState, useRef } from "react";
import { guestService } from "@/services/api/guest.service";
import { interestService } from "@/services/api/interest.service";
import { toast } from "sonner";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";

interface UserInfoModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  guestId: string;
}

export function UserInfoModal({
  open,
  onOpenChange,
  guestId,
}: UserInfoModalProps) {
  const [guestInfo, setGuestInfo] = useState<Conversation | null>(null);
  const [originalGuestInfo, setOriginalGuestInfo] =
    useState<Conversation | null>(null);
  const [editableFields, setEditableFields] = useState<Record<string, boolean>>(
    {
      fullname: false,
      gender: false,
      birthday: false,
      email: false,
      phone: false,
      address: false,
      interests: false,
    }
  );
  const [isSaving, setIsSaving] = useState(false);
  const [availableInterests, setAvailableInterests] = useState<Interest[]>([]);
  const [selectedInterestNames, setSelectedInterestNames] = useState<string[]>(
    []
  );
  const [isInterestsLoading, setIsInterestsLoading] = useState(false);
  const interestsContainerRef = useRef<HTMLDivElement>(null);
  const [isInterestsDropdownOpen, setIsInterestsDropdownOpen] = useState(false);

  const fetchGuestInfo = async (guestId: string) => {
    try {
      const response = await guestService.getGuestInfo(guestId);
      setGuestInfo(response);
      setOriginalGuestInfo(response);
      // Khởi tạo danh sách tên nhãn đã chọn từ danh sách interests (handle null)
      setSelectedInterestNames(
        response.interests?.map((interest) => interest.name) || []
      );
    } catch (error) {
      console.error("Error fetching guest info:", error);
      // Set guestInfo to null or a default structure if fetching fails
      setGuestInfo(null);
      setOriginalGuestInfo(null);
      setSelectedInterestNames([]);
    }
  };

  // Fetch tất cả nhãn từ API
  const fetchAllInterests = async () => {
    try {
      setIsInterestsLoading(true);
      const response = await interestService.getAllPublishedInterests();
      setAvailableInterests(response);
    } catch (error) {
      console.error("Error fetching interests:", error);
    } finally {
      setIsInterestsLoading(false);
    }
  };

  useEffect(() => {
    if (open && guestId) {
      // Fetch guest information when the modal opens
      fetchGuestInfo(guestId);
      // Fetch all interests when modal opens
      fetchAllInterests();
      // Reset editable fields when modal opens
      setEditableFields({
        fullname: false,
        gender: false,
        birthday: false,
        email: false,
        phone: false,
        address: false,
        interests: false,
      });
    }
  }, [open, guestId]);

  // Đóng dropdown khi click ra ngoài
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        interestsContainerRef.current &&
        !interestsContainerRef.current.contains(event.target as Node)
      ) {
        setIsInterestsDropdownOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Add a keyword to selected list
  const addInterest = (interestName: string) => {
    setSelectedInterestNames((prev) => [...prev, interestName]);
  };

  // Remove a keyword from selected list
  const removeInterest = (interestName: string) => {
    setSelectedInterestNames((prev) =>
      prev.filter((name) => name !== interestName)
    );
  };

  // Find interest object by name
  const getInterestByName = (name: string): Interest | undefined => {
    return availableInterests.find((interest) => interest.name === name);
  };

  const toggleEditField = (fieldName: string) => {
    setEditableFields((prev) => ({
      ...prev,
      [fieldName]: !prev[fieldName],
    }));
  };

  const resetField = (fieldName: keyof typeof editableFields) => {
    if (!originalGuestInfo || !guestInfo) return;

    // Use a temporary object to build the update for setGuestInfo
    let update: Partial<Conversation> = {};

    if (fieldName === "interests") {
      setSelectedInterestNames(
        originalGuestInfo.interests?.map((interest) => interest.name) || []
      );
      // Update guestInfo state for interests
      update.interests = originalGuestInfo.interests || [];
    } else if (fieldName === "gender") {
      const originalValue = originalGuestInfo.gender;
      // Map null back to 'unknown' for the Select component's value prop during reset
      update.gender = originalValue === null ? "unknown" : originalValue;
    } else if (fieldName === "birthday") {
      const originalValue = originalGuestInfo.birthday;
      // Reset to empty string for the date input if original was null
      update.birthday = originalValue === null ? "" : originalValue;
    } else if (
      fieldName === "fullname" ||
      fieldName === "email" ||
      fieldName === "phone" ||
      fieldName === "address"
    ) {
      // Access known string | null fields
      const originalValue = originalGuestInfo[fieldName];
      // Reset to empty string for Input if original was null
      update[fieldName] = originalValue === null ? "" : originalValue;
    }

    // Apply the update to guestInfo state
    setGuestInfo((prev) => ({
      ...prev!,
      ...update,
    }));

    toggleEditField(fieldName);
  };

  const handleInputChange = (
    fieldName: keyof typeof editableFields,
    value: string | null
  ) => {
    if (!guestInfo) return;

    // Determine the actual value to store in the state
    let actualValueToStore: string | null;

    if (fieldName === "gender") {
      // Map 'unknown' value from Select back to null for the state
      actualValueToStore = value === "unknown" ? null : value;
    } else {
      // Map empty string input to null for other fields
      actualValueToStore = value === "" ? null : value;
    }

    // Update the guestInfo state
    setGuestInfo((prev) => ({
      ...prev!,
      // Use computed property name to update the correct field
      [fieldName]: actualValueToStore,
    }));
  };

  const handleSave = async () => {
    if (!guestInfo) return;
    setIsSaving(true);
    try {
      // Lấy danh sách ID của các nhãn đã chọn
      const interestIds = selectedInterestNames
        .map((name) => {
          const interest = availableInterests.find((i) => i.name === name);
          return interest ? interest.id : null;
        })
        .filter((id): id is string => id !== null);

      // Ensure potentially null fields are handled correctly for the API
      const updateData: GuestInfoUpdate = {
        fullname: guestInfo.fullname || null,
        email: guestInfo.email || null,
        phone: guestInfo.phone || null,
        address: guestInfo.address || null,
        // Gender state is already null if "unknown" was selected
        gender: guestInfo.gender,
        // Ensure birthday is in ISO format or null
        birthday: guestInfo.birthday
          ? new Date(guestInfo.birthday).toISOString()
          : null,
        interest_ids: interestIds,
      };

      const updatedGuestInfo = await guestService.updateGuestInfo(
        guestId,
        updateData
      );
      // Update local state with potentially null values from API response
      // Map null gender back to "unknown" for the Select component if needed after save
      const displayGuestInfo = {
        ...updatedGuestInfo,
        // gender: updatedGuestInfo.gender === null ? 'unknown' : updatedGuestInfo.gender, // Not strictly needed if Select handles null->unknown
      };
      setGuestInfo(displayGuestInfo);
      setOriginalGuestInfo(displayGuestInfo); // Store potentially modified display state as original
      setSelectedInterestNames(
        updatedGuestInfo.interests?.map((i) => i.name) || []
      );

      // Show success toast
      toast.success("Lưu thông tin thành công");
      // reset all editable fields
      setEditableFields(
        Object.keys(editableFields).reduce(
          (acc, key) => ({ ...acc, [key]: false }),
          {}
        )
      );
      onOpenChange(false); // Close modal on successful save
    } catch (error) {
      console.error(error);
      toast.error("Không thể cập nhật thông tin");
    } finally {
      setIsSaving(false);
    }
  };

  // Helper to safely get date string for input type="date"
  const getSafeDateString = (
    isoDateString: string | null | undefined
  ): string => {
    if (!isoDateString) return "";
    try {
      return new Date(isoDateString).toISOString().slice(0, 10);
    } catch (e) {
      return ""; // Return empty string for invalid dates
    }
  };

  // Helper to safely format date for display
  const formatSafeDate = (isoDateString: string | null | undefined): string => {
    if (!isoDateString) return "N/A";
    try {
      return new Date(isoDateString).toLocaleDateString("vi-VN");
    } catch (e) {
      return "Invalid Date";
    }
  };

  return (
    // Keep guestInfo !== null check or adjust based on desired behavior when loading/error
    guestInfo !== null && (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogTitle className="text-center text-lg font-bold"></DialogTitle>
        <DialogContent className="sm:max-w-[850px] h-full p-0 overflow-auto">
          <div className="flex flex-col items-center pt-8 pb-6 bg-white">
            <div className="relative">
              <Avatar className="h-24 w-24 border-2 border-[#6366F1]">
                {/* Use AvatarFallback for missing avatar */}
                {guestInfo.avatar ? (
                  <img
                    src={guestInfo.avatar}
                    alt="User avatar"
                    className="object-cover h-full w-full" // Ensure image covers avatar area
                  />
                ) : (
                  <AvatarFallback className="text-4xl">
                    {guestInfo.account_name?.charAt(0).toUpperCase() || "?"}
                  </AvatarFallback>
                )}
              </Avatar>
              {/* Online indicator can remain */}
              <div className="absolute bottom-0 right-0 h-5 w-5 rounded-full bg-[#0084FF] border-2 border-white"></div>
            </div>

            <h2 className="text-2xl font-bold mt-4">
              {guestInfo.account_name || "Khách hàng"}{" "}
              {/* Fallback for account_name */}
            </h2>
          </div>

          <div className="p-6 space-y-4">
            {/* Fullname */}
            <div className="flex items-center justify-between">
              <div className="w-[120px] font-medium">Tên:</div>
              <div className="flex-1 flex items-center">
                <Input
                  value={guestInfo.fullname || ""} // Use empty string for null
                  placeholder="Chưa có thông tin"
                  className={`flex-1 ${
                    !editableFields.fullname ? "bg-gray-50" : "bg-white"
                  }`}
                  readOnly={!editableFields.fullname}
                  onChange={(e) =>
                    handleInputChange("fullname", e.target.value)
                  }
                />
                {/* Edit/Reset Button */}
                <Button
                  variant="ghost"
                  size="icon"
                  className="ml-2 h-8 w-8 text-gray-500"
                  onClick={() =>
                    editableFields.fullname
                      ? resetField("fullname")
                      : toggleEditField("fullname")
                  }
                >
                  {editableFields.fullname ? (
                    <RotateCcw className="h-4 w-4" />
                  ) : (
                    <Edit className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            {/* Gender */}
            <div className="flex items-center justify-between">
              <div className="w-[120px] font-medium">Giới tính:</div>
              <div className="flex-1 flex items-center">
                <Select
                  // Map null gender state to "unknown" for the Select value
                  value={guestInfo.gender || "unknown"}
                  onValueChange={(value) => handleInputChange("gender", value)}
                  disabled={!editableFields.gender}
                >
                  <SelectTrigger
                    className={`flex-1 ${
                      !editableFields.gender ? "bg-gray-50" : "bg-white"
                    }`}
                  >
                    <SelectValue placeholder="Chọn giới tính" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="male">Nam</SelectItem>
                    <SelectItem value="female">Nữ</SelectItem>
                    {/* Use "unknown" instead of "" for the value */}
                    <SelectItem value="unknown">Không xác định</SelectItem>
                  </SelectContent>
                </Select>
                {/* Edit/Reset Button */}
                <Button
                  variant="ghost"
                  size="icon"
                  className="ml-2 h-8 w-8 text-gray-500"
                  onClick={() =>
                    editableFields.gender
                      ? resetField("gender")
                      : toggleEditField("gender")
                  }
                >
                  {editableFields.gender ? (
                    <RotateCcw className="h-4 w-4" />
                  ) : (
                    <Edit className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            {/* Birthday */}
            <div className="flex items-center justify-between">
              <div className="w-[120px] font-medium">Năm sinh:</div>
              <div className="flex-1 flex items-center">
                {editableFields.birthday ? (
                  <Input
                    type="date"
                    value={getSafeDateString(guestInfo.birthday)} // Use helper
                    className="flex-1 bg-white"
                    onChange={(e) =>
                      handleInputChange(
                        // Convert date string back to ISO string or null if empty
                        "birthday",
                        e.target.value
                          ? new Date(e.target.value).toISOString()
                          : null
                      )
                    }
                  />
                ) : (
                  <Input
                    value={formatSafeDate(guestInfo.birthday)} // Use helper for display
                    readOnly
                    className="flex-1 bg-gray-50"
                  />
                )}
                {/* Edit/Reset Button */}
                <Button
                  variant="ghost"
                  size="icon"
                  className="ml-2 h-8 w-8 text-gray-500"
                  onClick={() =>
                    editableFields.birthday
                      ? resetField("birthday")
                      : toggleEditField("birthday")
                  }
                >
                  {editableFields.birthday ? (
                    <RotateCcw className="h-4 w-4" />
                  ) : (
                    <Edit className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            {/* Email */}
            <div className="flex items-center justify-between">
              <div className="w-[120px] font-medium">Email:</div>
              <div className="flex-1 flex items-center">
                <Input
                  value={guestInfo.email || ""} // Use empty string for null
                  placeholder="Chưa có thông tin"
                  className={`flex-1 ${
                    !editableFields.email ? "bg-gray-50" : "bg-white"
                  }`}
                  readOnly={!editableFields.email}
                  onChange={(e) => handleInputChange("email", e.target.value)}
                />
                {/* Edit/Reset Button */}
                <Button
                  variant="ghost"
                  size="icon"
                  className="ml-2 h-8 w-8 text-gray-500"
                  onClick={() =>
                    editableFields.email
                      ? resetField("email")
                      : toggleEditField("email")
                  }
                >
                  {editableFields.email ? (
                    <RotateCcw className="h-4 w-4" />
                  ) : (
                    <Edit className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            {/* Phone */}
            <div className="flex items-center justify-between">
              <div className="w-[120px] font-medium">SĐT:</div>
              <div className="flex-1 flex items-center">
                <Input
                  value={guestInfo.phone || ""} // Use empty string for null
                  placeholder="Chưa có thông tin"
                  className={`flex-1 ${
                    !editableFields.phone ? "bg-gray-50" : "bg-white"
                  }`}
                  readOnly={!editableFields.phone}
                  onChange={(e) => handleInputChange("phone", e.target.value)}
                />
                {/* Edit/Reset Button */}
                <Button
                  variant="ghost"
                  size="icon"
                  className="ml-2 h-8 w-8 text-gray-500"
                  onClick={() =>
                    editableFields.phone
                      ? resetField("phone")
                      : toggleEditField("phone")
                  }
                >
                  {editableFields.phone ? (
                    <RotateCcw className="h-4 w-4" />
                  ) : (
                    <Edit className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            {/* Address */}
            <div className="flex items-center justify-between">
              <div className="w-[120px] font-medium">Địa chỉ:</div>
              <div className="flex-1 flex items-center">
                <Input
                  value={guestInfo.address || ""} // Use empty string for null
                  placeholder="Chưa có thông tin"
                  className={`flex-1 ${
                    !editableFields.address ? "bg-gray-50" : "bg-white"
                  }`}
                  readOnly={!editableFields.address}
                  onChange={(e) => handleInputChange("address", e.target.value)}
                />
                {/* Edit/Reset Button */}
                <Button
                  variant="ghost"
                  size="icon"
                  className="ml-2 h-8 w-8 text-gray-500"
                  onClick={() =>
                    editableFields.address
                      ? resetField("address")
                      : toggleEditField("address")
                  }
                >
                  {editableFields.address ? (
                    <RotateCcw className="h-4 w-4" />
                  ) : (
                    <Edit className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            {/* Interests */}
            <div className="flex items-center justify-between">
              <div className="w-[120px] font-medium">Nhãn:</div>
              <div className="flex-1 flex items-center">
                <div className="flex-1 relative" ref={interestsContainerRef}>
                  <div
                    className={`flex flex-wrap min-h-10 max-h-24 overflow-y-auto px-3 py-2 border rounded-md ${
                      isInterestsDropdownOpen
                        ? "border-[#6366F1] ring-2 ring-[#6366F1]/20"
                        : "border-input"
                    } ${
                      !editableFields.interests ? "bg-gray-50" : "bg-white"
                    } gap-1 cursor-pointer`}
                    onClick={() => {
                      if (editableFields.interests) {
                        setIsInterestsDropdownOpen(true);
                      }
                    }}
                  >
                    {/* Check if selectedInterestNames has items */}
                    {selectedInterestNames.length > 0 ? (
                      selectedInterestNames.map((interestName) => {
                        const interest = getInterestByName(interestName);
                        const color = interest?.color || "#6366F1"; // Default color if interest not found

                        return (
                          <Badge
                            key={interestName}
                            className="mb-1 inline-flex"
                            style={{
                              backgroundColor: `${color}20`, // 20% opacity
                              color: color,
                              borderColor: `${color}30`, // 30% opacity
                            }}
                          >
                            {interestName}
                            {editableFields.interests && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-4 w-4 p-0 ml-1 hover:bg-transparent"
                                onClick={(e) => {
                                  e.stopPropagation(); // Prevent opening dropdown
                                  removeInterest(interestName);
                                }}
                              >
                                <X className="h-3 w-3" />
                              </Button>
                            )}
                          </Badge>
                        );
                      })
                    ) : (
                      <span className="text-muted-foreground text-sm">
                        {editableFields.interests
                          ? "Chọn nhãn..."
                          : "Không có nhãn"}
                      </span>
                    )}
                  </div>

                  {/* Dropdown for adding interests */}
                  {isInterestsDropdownOpen && editableFields.interests && (
                    <div className="absolute z-50 w-full mt-1 bg-white border rounded-md shadow-lg max-h-60 overflow-auto">
                      {isInterestsLoading ? (
                        <div className="px-3 py-2 text-center">Đang tải...</div>
                      ) : availableInterests.filter(
                          (interest) =>
                            !selectedInterestNames.includes(interest.name)
                        ).length > 0 ? (
                        availableInterests
                          .filter(
                            (interest) =>
                              !selectedInterestNames.includes(interest.name)
                          )
                          .map((interest) => (
                            <div
                              key={interest.id}
                              className="px-3 py-2 hover:bg-slate-100 cursor-pointer flex items-center"
                              onClick={() => {
                                addInterest(interest.name);
                                // Close dropdown if it was the last available interest
                                if (
                                  availableInterests.filter(
                                    (i) =>
                                      !selectedInterestNames.includes(i.name) &&
                                      i.name !== interest.name // Exclude the one just added
                                  ).length === 0
                                ) {
                                  setIsInterestsDropdownOpen(false);
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
                          Không có nhãn nào để thêm
                        </div>
                      )}
                    </div>
                  )}
                </div>
                {/* Edit/Reset Button */}
                <Button
                  variant="ghost"
                  size="icon"
                  className="ml-2 h-8 w-8 text-gray-500"
                  onClick={
                    () =>
                      editableFields.interests
                        ? (() => {
                            // Reset interests to original state
                            resetField("interests"); // Use resetField logic
                            setIsInterestsDropdownOpen(false); // Close dropdown on reset
                          })()
                        : toggleEditField("interests") // Enter edit mode
                  }
                >
                  {editableFields.interests ? (
                    <RotateCcw className="h-4 w-4" />
                  ) : (
                    <Edit className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-center gap-4 p-6 pt-2">
            <Button
              variant="outline"
              className="w-24"
              onClick={() => {
                // Reset all fields to original state before closing if changes were made
                if (originalGuestInfo) {
                  setGuestInfo(originalGuestInfo);
                  setSelectedInterestNames(
                    originalGuestInfo.interests?.map((i) => i.name) || []
                  );
                }
                onOpenChange(false); // Close modal
              }}
              disabled={isSaving}
            >
              Hủy
            </Button>
            <Button
              className="w-24 bg-[#6366F1] hover:bg-[#4F46E5]"
              onClick={handleSave}
              disabled={
                isSaving || !Object.values(editableFields).some(Boolean)
              } // Disable save if not saving and no fields are being edited
            >
              {isSaving ? "Đang lưu..." : "Lưu"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    )
  );
}
