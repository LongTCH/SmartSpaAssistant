import { Interest } from "./interest";

export interface GuestInfoUpdate {
  fullname: string;
  email: string;
  phone: string;
  address: string;
  gender: string;
  birthday: string;
  interest_ids: string[];
}
