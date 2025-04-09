"use server";

import { stateParamSchema, AuthResponse } from "@/schemas/auth";
import { authService } from "@/services/api/auth.service";

type ExchangeStateResponse = {
  success: boolean;
  data?: AuthResponse;
  error?: string;
};

export async function exchangeStateAction(
  state: string
): Promise<ExchangeStateResponse> {
  const stateValidation = stateParamSchema.safeParse(state);
  if (!stateValidation.success) {
    console.error("Invalid state parameter:", stateValidation.error);
    return {
      success: false,
      error: "Invalid state parameter",
    };
  }

  try {
    const authData = await authService.exchangeState(stateValidation.data);

    return {
      success: true,
      data: authData,
    };
  } catch (error: any) {
    console.error("State exchange error:", error);
    
    return {
      success: false,
      error: error.message || "Failed to authenticate. Please try again.",
    };
  }
}
