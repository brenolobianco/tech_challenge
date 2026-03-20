import axios from "axios";
import { UploadResponse, UploadStatus } from "./types/upload";
import { CampaignSummary, CampaignDetailResponse } from "./types/campaign";
import { UserData } from "./types/user";
import { PaginatedResponse } from "./types/common";

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
});

export async function uploadCSV(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const resp = await api.post("/upload", formData);
  return resp.data;
}

export async function getUploadStatus(uploadId: string): Promise<UploadStatus> {
  const resp = await api.get(`/upload/${uploadId}/status`);
  return resp.data;
}

export function streamUploadStatus(
  uploadId: string,
  onMessage: (data: Record<string, any>) => void,
  onError?: (err: Event) => void
): EventSource {
  const eventSource = new EventSource(`${BASE_URL}/upload/${uploadId}/stream`);

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);

    if (data.status === "completed" || data.status === "failed") {
      eventSource.close();
    }
  };

  eventSource.onerror = (err) => {
    if (onError) onError(err);
    eventSource.close();
  };

  return eventSource;
}

export async function getCampaigns(
  page = 1,
  pageSize = 20,
  uploadId?: string
): Promise<PaginatedResponse<CampaignSummary>> {
  const params: Record<string, string | number> = { page, page_size: pageSize };
  if (uploadId) params.upload_id = uploadId;
  const resp = await api.get("/campaigns", { params });
  return resp.data;
}

export async function getCampaignDetail(
  id: number,
  page = 1,
  pageSize = 20
): Promise<CampaignDetailResponse> {
  const resp = await api.get(`/campaigns/${id}`, {
    params: { page, page_size: pageSize },
  });
  return resp.data;
}

export async function getUsers(
  page = 1,
  pageSize = 20,
  filters: Record<string, string | number> = {}
): Promise<PaginatedResponse<UserData>> {
  const resp = await api.get("/users", {
    params: { page, page_size: pageSize, ...filters },
  });
  return resp.data;
}
