export interface RowError {
  row: number;
  field: string;
  message: string;
}

export interface UploadResponse {
  upload_id: string;
  status: string;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  errors: RowError[];
}

export interface UploadStatus {
  upload_id: string;
  status: string;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  created_at: string;
  processed_at: string | null;
}
