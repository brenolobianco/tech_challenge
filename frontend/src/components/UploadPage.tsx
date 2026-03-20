import React, { useState, useCallback, useEffect, useRef } from "react";
import { uploadCSV, streamUploadStatus } from "../api";
import { UploadResponse, UploadStatus } from "../types";
import styles from "./UploadPage.module.css";

const UploadPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [status, setStatus] = useState<UploadStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    return () => { mountedRef.current = false; };
  }, []);

  const handleFile = (f: File | null) => {
    if (f && !f.name.endsWith(".csv")) {
      setError("Please select a .csv file");
      return;
    }
    setFile(f);
    setError(null);
  };

  const handleUpload = useCallback(async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setResult(null);
    setStatus(null);
    try {
      const resp = await uploadCSV(file);
      setResult(resp);
    } catch (err: any) {
      const detail = err.response?.data?.detail ?? err.response?.data;
      setError(detail?.message || detail || "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  }, [file]);

  useEffect(() => {
    if (!result) return;
    if (result.status !== "processing") return;

    const eventSource = streamUploadStatus(
      result.upload_id,
      (data) => {
        if (!mountedRef.current) return;
        setStatus({
          upload_id: data.upload_id,
          status: data.status,
          total_rows: data.total_rows ?? result.total_rows,
          valid_rows: data.valid_rows ?? result.valid_rows,
          invalid_rows: data.invalid_rows ?? result.invalid_rows,
          created_at: data.created_at ?? "",
          processed_at: data.processed_at ?? null,
        });
      },
      () => {
        // SSE connection closed or unavailable
      }
    );

    return () => eventSource.close();
  }, [result]);

  const currentStatus = status?.status || result?.status;

  const statusBadgeClass = `${styles.statusBadge} ${
    currentStatus === "completed"
      ? styles.statusCompleted
      : currentStatus === "failed"
      ? styles.statusFailed
      : styles.statusProcessing
  }`;

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const f = e.dataTransfer.files?.[0] || null;
    handleFile(f);
  };

  return (
    <div className={styles.page}>
      <h2>Upload CSV</h2>

      <div
        className={dragActive ? styles.dropzoneActive : styles.dropzone}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === "Enter") inputRef.current?.click(); }}
        aria-label="Upload CSV file"
      >
        <span className={styles.dropzoneIcon}>&#128206;</span>
        <p className={styles.dropzoneText}>
          {dragActive ? "Drop your file here" : "Drag & drop your CSV file here"}
        </p>
        <p className={styles.dropzoneHint}>or click to browse</p>
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          style={{ display: "none" }}
          onChange={(e) => handleFile(e.target.files?.[0] || null)}
        />
        {file && (
          <span className={styles.fileName}>
            &#128196; {file.name}
          </span>
        )}
      </div>

      <button
        className={styles.uploadButton}
        onClick={handleUpload}
        disabled={!file || uploading}
      >
        {uploading ? "Processing..." : "Upload & Generate Campaigns"}
      </button>

      {error && <div className={styles.error}>{error}</div>}

      {result && (
        <div className={styles.resultCard}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h3 style={{ margin: 0 }}>Upload Result</h3>
            <span className={statusBadgeClass}>{currentStatus}</span>
          </div>

          <p className={styles.uploadId}>ID: {result.upload_id}</p>

          <div className={styles.statsGrid}>
            <div className={styles.statBox}>
              <span className={styles.statValue}>{result.total_rows}</span>
              <span className={styles.statLabel}>Total Rows</span>
            </div>
            <div className={`${styles.statBox} ${styles.statBoxValid}`}>
              <span className={styles.statValue}>{result.valid_rows}</span>
              <span className={styles.statLabel}>Valid</span>
            </div>
            <div className={`${styles.statBox} ${styles.statBoxInvalid}`}>
              <span className={styles.statValue}>{result.invalid_rows}</span>
              <span className={styles.statLabel}>Invalid</span>
            </div>
          </div>

          {result.errors.length > 0 && (
            <div className={styles.errorsSection}>
              <h4>Validation Errors</h4>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th className={styles.th}>Row</th>
                    <th className={styles.th}>Field</th>
                    <th className={styles.th}>Message</th>
                  </tr>
                </thead>
                <tbody>
                  {result.errors.map((err, i) => (
                    <tr key={i} className={styles.tr}>
                      <td className={styles.td}>{err.row}</td>
                      <td className={styles.td}>{err.field}</td>
                      <td className={styles.td}>{err.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default UploadPage;
