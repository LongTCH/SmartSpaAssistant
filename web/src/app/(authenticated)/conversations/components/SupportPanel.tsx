"use client";

import { useEffect, useRef, useState } from "react";
import { guestService } from "@/services/api/guest.service";
import { interestService } from "@/services/api/interest.service";
import type { Conversation as BaseConversation } from "@/types/conversation";
import type { GuestInfo, GuestInfoUpdate } from "@/types/guest";
import type { Interest } from "@/types/interest";
import { toast } from "sonner";

// Import editable row components
import { EditableInputRow } from "../../../../components/guest-info/modal-parts/EditableInputRow";
import { EditableGenderRow } from "../../../../components/guest-info/modal-parts/EditableGenderRow";
import { EditableBirthdayRow } from "../../../../components/guest-info/modal-parts/EditableBirthdayRow";
import { EditableInterestsRow } from "../../../../components/guest-info/modal-parts/EditableInterestsRow";
import { Button } from "@/components/ui/button";

// Define the type where 'info' is mandatory
interface LoadedConversation extends Omit<BaseConversation, "info"> {
  info: GuestInfo;
}

const defaultGuestInfo: GuestInfo = {
  fullname: null,
  email: null,
  phone: null,
  address: null,
  gender: null,
  birthday: null,
};

interface SupportPanelProps {
  conversationId: string | null;
  onGuestInfoUpdated?: (updatedConversation: BaseConversation) => void; // Added this line
}

export default function SupportPanel({
  conversationId,
  onGuestInfoUpdated,
}: SupportPanelProps) {
  // Modified this line
  const [guestInfo, setGuestInfo] = useState<LoadedConversation | null>(null);
  const [originalGuestInfo, setOriginalGuestInfo] =
    useState<LoadedConversation | null>(null);
  const [isLoading, setIsLoading] = useState(true);

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
  const interestsContainerRef = useRef<HTMLDivElement | null>(null);
  const [isInterestsDropdownOpen, setIsInterestsDropdownOpen] = useState(false);
  const loadingInterestsRef = useRef(false); // Prevent concurrent interests API calls

  const fetchGuestInfo = async (guestId: string) => {
    try {
      setIsLoading(true);
      const response = await guestService.getGuestInfo(guestId);
      const loadedData: LoadedConversation = {
        ...response,
        info: response.info ?? defaultGuestInfo,
      };
      setGuestInfo(loadedData);
      setOriginalGuestInfo(loadedData);
      setSelectedInterestNames(
        response.interests?.map((interest) => interest.name) || []
      );
      // Reset editable fields when new guest info is loaded
      setEditableFields({
        fullname: false,
        gender: false,
        birthday: false,
        email: false,
        phone: false,
        address: false,
        interests: false,
      });
      setIsInterestsDropdownOpen(false);
    } catch {
      toast.error("Không thể tải thông tin khách hàng.");
      setGuestInfo(null);
      setOriginalGuestInfo(null);
      setSelectedInterestNames([]);
    } finally {
      setIsLoading(false);
    }
  };
  const fetchAllInterests = async () => {
    // Prevent concurrent API calls
    if (loadingInterestsRef.current) return;

    try {
      loadingInterestsRef.current = true;
      setIsInterestsLoading(true);
      const response = await interestService.getAllPublishedInterests();
      setAvailableInterests(response);
    } catch {
      toast.error("Không thể tải danh sách sở thích.");
    } finally {
      setIsInterestsLoading(false);
      loadingInterestsRef.current = false;
    }
  };

  useEffect(() => {
    if (conversationId) {
      fetchGuestInfo(conversationId);
      fetchAllInterests();
    } else {
      setGuestInfo(null);
      setOriginalGuestInfo(null);
      setSelectedInterestNames([]);
      setAvailableInterests([]);
      setIsLoading(false); // Ensure loading is false if no ID
      setEditableFields({
        fullname: false,
        gender: false,
        birthday: false,
        email: false,
        phone: false,
        address: false,
        interests: false,
      });
      setIsInterestsDropdownOpen(false);
    }
  }, [conversationId]);

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

  const addInterest = (interestName: string) => {
    setSelectedInterestNames((prev) => [...prev, interestName]);
  };

  const removeInterest = (interestName: string) => {
    setSelectedInterestNames((prev) =>
      prev.filter((name) => name !== interestName)
    );
  };

  const toggleEditField = (fieldName: string) => {
    setEditableFields((prev) => ({
      ...prev,
      [fieldName]: !prev[fieldName],
    }));
    if (fieldName === "interests" && !editableFields.interests) {
      setIsInterestsDropdownOpen(true);
    }
    if (fieldName === "interests" && editableFields.interests) {
      setIsInterestsDropdownOpen(false);
    }
  };

  const resetField = (fieldName: keyof typeof editableFields) => {
    if (!originalGuestInfo || !guestInfo) return;

    setGuestInfo((prev) => {
      if (!prev) return prev;
      const newInfo = { ...prev.info };
      let newInterests = prev.interests;

      if (fieldName === "interests") {
        setSelectedInterestNames(
          originalGuestInfo.interests?.map((interest) => interest.name) || []
        );
        newInterests = originalGuestInfo.interests || [];
      } else {
        if (fieldName === "gender") {
          newInfo.gender = originalGuestInfo.info.gender;
        } else if (fieldName === "birthday") {
          newInfo.birthday = originalGuestInfo.info.birthday;
        } else if (
          fieldName === "fullname" ||
          fieldName === "email" ||
          fieldName === "phone" ||
          fieldName === "address"
        ) {
          newInfo[fieldName as keyof GuestInfo] =
            originalGuestInfo.info[fieldName as keyof GuestInfo];
        }
      }
      return { ...prev, info: newInfo, interests: newInterests };
    });
    toggleEditField(fieldName); // Close edit mode for the field
  };

  const handleInputChange = (
    fieldName: keyof Omit<typeof editableFields, "interests">,
    value: string | null
  ) => {
    setGuestInfo((prev) => {
      if (!prev) return prev;
      let actualValueToStore: string | null;
      if (fieldName === "gender") {
        actualValueToStore = value === "unknown" ? null : value;
      } else {
        actualValueToStore = value === "" ? null : value;
      }
      const newInfo = { ...prev.info, [fieldName]: actualValueToStore };
      return { ...prev, info: newInfo };
    });
  };

  const handleSave = async () => {
    if (!guestInfo || !conversationId) return;
    setIsSaving(true);
    try {
      const interestIds = selectedInterestNames
        .map((name) => {
          const interest = availableInterests.find((i) => i.name === name);
          return interest ? interest.id : null;
        })
        .filter((id): id is string => id !== null);

      const currentInfo = guestInfo.info;
      const updateData: GuestInfoUpdate = {
        fullname: currentInfo.fullname,
        email: currentInfo.email,
        phone: currentInfo.phone,
        address: currentInfo.address,
        gender: currentInfo.gender,
        birthday: currentInfo.birthday
          ? new Date(currentInfo.birthday).toISOString()
          : null,
        interest_ids: interestIds,
      };

      const updatedConversationResponse = await guestService.updateGuestInfo(
        conversationId,
        updateData
      );
      const ensuredUpdatedConversation: LoadedConversation = {
        ...updatedConversationResponse,
        info: updatedConversationResponse.info ?? defaultGuestInfo,
      };

      setGuestInfo(ensuredUpdatedConversation);
      setOriginalGuestInfo(ensuredUpdatedConversation);
      setSelectedInterestNames(
        ensuredUpdatedConversation.interests?.map((i) => i.name) || []
      );

      toast.success("Lưu thông tin thành công");
      setEditableFields(
        Object.keys(editableFields).reduce(
          (acc, key) => ({ ...acc, [key]: false }),
          {}
        )
      );
      setIsInterestsDropdownOpen(false);

      if (onGuestInfoUpdated) {
        // Added this block
        onGuestInfoUpdated(ensuredUpdatedConversation);
      }
    } catch {
      toast.error("Không thể cập nhật thông tin");
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    if (originalGuestInfo) {
      setGuestInfo(originalGuestInfo);
      setSelectedInterestNames(
        originalGuestInfo.interests?.map((i) => i.name) || []
      );
    }
    setEditableFields(
      Object.keys(editableFields).reduce(
        (acc, key) => ({ ...acc, [key]: false }),
        {}
      )
    );
    setIsInterestsDropdownOpen(false);
  };

  const getSafeDateString = (
    isoDateString: string | null | undefined
  ): string => {
    if (!isoDateString) return "";
    try {
      const date = new Date(isoDateString);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, "0");
      const day = String(date.getDate()).padStart(2, "0");
      return `${year}-${month}-${day}`;
    } catch {
      return "";
    }
  };

  const formatSafeDate = (isoDateString: string | null | undefined): string => {
    if (!isoDateString) return "N/A";
    try {
      return new Date(isoDateString).toLocaleDateString();
    } catch {
      return "Invalid Date";
    }
  };

  if (isLoading) {
    return (
      <div className="w-80 border-l border-border bg-card h-full p-4 flex flex-col">
        <div className="animate-pulse">
          <div className="h-20 bg-muted rounded-md mb-4"></div>
          <div className="h-6 bg-muted rounded-md mb-2 w-3/4"></div>
          <div className="h-4 bg-muted rounded-md mb-4 w-1/2"></div>
          <div className="space-y-2 mt-4">
            {[1, 2, 3, 4, 5].map((index) => (
              <div key={index} className="h-8 bg-muted rounded-md"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!guestInfo) {
    return (
      <div className="w-80 border-l border-border bg-card h-full p-4 flex flex-col items-center justify-center">
        <p className="text-muted-foreground">
          Select a conversation to view guest details
        </p>
      </div>
    );
  }

  const canSaveChanges =
    Object.values(editableFields).some(Boolean) ||
    JSON.stringify(guestInfo) !== JSON.stringify(originalGuestInfo) ||
    JSON.stringify(selectedInterestNames.sort()) !==
      JSON.stringify(
        originalGuestInfo?.interests?.map((i) => i.name).sort() || []
      );

  return (
    <div className="w-80 border-l border-border bg-card h-full flex flex-col">
      {/* <div className="overflow-y-auto flex-grow p-0"> */}
      {/* GuestInfoHeader removed */}
      {/* </div> */}
      {/* <div className="text-center py-4 border-b border-border">
        <h2 className="text-xl font-semibold">
          {guestInfo.account_name || "Khách hàng"}
        </h2>
      </div> */}

      <div className="overflow-y-auto flex-grow p-4 space-y-3">
        {/* Adjusted padding and spacing */}
        <EditableInputRow
          label="Tên"
          value={guestInfo.info.fullname}
          placeholder="Chưa có thông tin"
          isEditable={editableFields.fullname}
          fieldName="fullname"
          onInputChange={handleInputChange}
          onToggleEdit={toggleEditField}
          onReset={resetField}
        />
        <EditableGenderRow
          label="Giới tính"
          value={guestInfo.info.gender}
          isEditable={editableFields.gender}
          fieldName="gender"
          onValueChange={handleInputChange}
          onToggleEdit={toggleEditField}
          onReset={resetField}
        />
        <EditableBirthdayRow
          label="Năm sinh"
          value={guestInfo.info.birthday}
          isEditable={editableFields.birthday}
          fieldName="birthday"
          onInputChange={handleInputChange}
          onToggleEdit={toggleEditField}
          onReset={resetField}
          getSafeDateString={getSafeDateString}
          formatSafeDate={formatSafeDate}
        />
        <EditableInputRow
          label="Email"
          value={guestInfo.info.email}
          placeholder="Chưa có thông tin"
          isEditable={editableFields.email}
          fieldName="email"
          onInputChange={handleInputChange}
          onToggleEdit={toggleEditField}
          onReset={resetField}
        />
        <EditableInputRow
          label="SĐT"
          value={guestInfo.info.phone}
          placeholder="Chưa có thông tin"
          isEditable={editableFields.phone}
          fieldName="phone"
          onInputChange={handleInputChange}
          onToggleEdit={toggleEditField}
          onReset={resetField}
        />
        <EditableInputRow
          label="Địa chỉ"
          value={guestInfo.info.address}
          placeholder="Chưa có thông tin"
          isEditable={editableFields.address}
          fieldName="address"
          onInputChange={handleInputChange}
          onToggleEdit={toggleEditField}
          onReset={resetField}
        />
        <EditableInterestsRow
          label="Nhãn"
          isEditable={editableFields.interests}
          fieldName="interests"
          onToggleEdit={toggleEditField}
          onReset={resetField}
          selectedInterestNames={selectedInterestNames}
          availableInterests={availableInterests}
          addInterest={addInterest}
          removeInterest={removeInterest}
          isInterestsLoading={isInterestsLoading}
          isInterestsDropdownOpen={isInterestsDropdownOpen}
          setIsInterestsDropdownOpen={setIsInterestsDropdownOpen}
          interestsContainerRef={interestsContainerRef}
        />
      </div>

      <div className="p-2 mt-auto border-t border-border flex justify-end space-x-1 sticky bottom-0 bg-card z-10">
        <Button
          onClick={handleSave}
          disabled={isSaving || !canSaveChanges}
          className="text-xs px-2 py-1 h-auto bg-blue-500 hover:bg-blue-600 text-white" /* Further reduced padding, added blue color */
        >
          {isSaving ? "Đang lưu..." : "Lưu"} {/* Shortened text */}
        </Button>
        <Button
          onClick={handleCancel}
          disabled={isSaving}
          className="text-xs px-2 py-1 h-auto bg-gray-200 text-gray-800 hover:bg-gray-300" /* Further reduced padding, added gray color, removed variant="outline" */
        >
          Hủy {/* Already short */}
        </Button>
      </div>
    </div>
  );
}
