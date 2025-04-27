import apiClient from "@/lib/axios";
import { API_ROUTES } from "@/lib/constants";
import { SettingsState } from "@/types";

export const settingsService = {
  /**
   * Get application settings
   * @returns Application settings
   */
  async getSettings(): Promise<SettingsState> {
    const response = await apiClient.instance.get(API_ROUTES.SETTING.GET);
    return response.data as SettingsState;
  },

  /**
   * Update application settings
   * @param settings - Updated settings object
   * @returns Updated settings
   */
  async updateSettings(settings: SettingsState): Promise<SettingsState> {
    const response = await apiClient.instance.put(
      API_ROUTES.SETTING.UPDATE,
      settings
    );
    return response.data as SettingsState;
  },
};

export default settingsService;
