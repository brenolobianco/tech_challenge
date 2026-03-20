import { UserData } from "./user";
import { PaginatedResponse } from "./common";

export interface CampaignSummary {
  id: number;
  name: string;
  users_count: number;
  average_income: number;
}

export interface CampaignDetailResponse {
  campaign: CampaignSummary;
  users: PaginatedResponse<UserData>;
}
