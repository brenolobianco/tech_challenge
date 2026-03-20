import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getCampaigns } from "../api";
import { CampaignSummary } from "../types";
import styles from "./CampaignsPage.module.css";

const CampaignsPage: React.FC = () => {
  const [campaigns, setCampaigns] = useState<CampaignSummary[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pageSize = 20;
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    setError(null);
    getCampaigns(page, pageSize)
      .then((resp) => {
        setCampaigns(resp.data);
        setTotal(resp.total);
      })
      .catch(() => {
        setError("Failed to load campaigns.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [page]);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      <h2>Campaigns</h2>

      {error && <div className={styles.error}>{error}</div>}

      {loading ? (
        <div className={styles.empty}>Loading campaigns...</div>
      ) : campaigns.length === 0 ? (
        <div className={styles.empty}>
          <span className={styles.emptyIcon}>&#128203;</span>
          No campaigns found. Upload a CSV to generate campaigns.
        </div>
      ) : (
        <div className={styles.grid}>
          {campaigns.map((c) => (
            <div
              key={c.id}
              className={styles.card}
              onClick={() => navigate(`/campaigns/${c.id}`)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => { if (e.key === "Enter") navigate(`/campaigns/${c.id}`); }}
            >
              <div className={styles.cardName}>{c.name}</div>
              <div className={styles.cardStats}>
                <div className={styles.cardStat}>
                  <span className={styles.cardStatValue}>{c.users_count}</span>
                  <span className={styles.cardStatLabel}>Users</span>
                </div>
                <div className={styles.cardStat}>
                  <span className={styles.cardStatValue}>
                    ${c.average_income.toFixed(0)}
                  </span>
                  <span className={styles.cardStatLabel}>Avg Income</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <div className={styles.pagination}>
          <button disabled={page <= 1} onClick={() => setPage(page - 1)}>
            Previous
          </button>
          <span className={styles.pageInfo}>
            Page {page} of {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default CampaignsPage;
