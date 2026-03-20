import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getCampaignDetail } from "../api";
import { CampaignSummary, UserData } from "../types";
import styles from "./CampaignDetailPage.module.css";

const CampaignDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [campaign, setCampaign] = useState<CampaignSummary | null>(null);
  const [users, setUsers] = useState<UserData[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pageSize = 20;

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    getCampaignDetail(Number(id), page, pageSize)
      .then((resp) => {
        setCampaign(resp.campaign);
        setUsers(resp.users.data);
        setTotal(resp.users.total);
      })
      .catch(() => {
        setError("Failed to load campaign details.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [id, page]);

  const totalPages = Math.ceil(total / pageSize);

  if (loading) return <p className={styles.loading}>Loading...</p>;
  if (error) return <p className={styles.loading}>{error}</p>;
  if (!campaign) return <p className={styles.loading}>Campaign not found.</p>;

  return (
    <div>
      <div className={styles.header}>
        <button onClick={() => navigate("/campaigns")} className={styles.backButton}>
          &larr; Back
        </button>
        <h2 className={styles.title}>{campaign.name}</h2>
      </div>

      <div className={styles.statsRow}>
        <div className={styles.statCard}>
          <span className={styles.statValue}>{campaign.users_count}</span>
          <span className={styles.statLabel}>Users</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statValue}>${campaign.average_income.toFixed(2)}</span>
          <span className={styles.statLabel}>Avg Income</span>
        </div>
      </div>

      <div className={styles.tableCard}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th className={styles.th}>ID</th>
              <th className={styles.th}>Name</th>
              <th className={styles.th}>Age</th>
              <th className={styles.th}>City</th>
              <th className={styles.th}>Income</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className={styles.tr}>
                <td className={styles.td}>{u.original_id}</td>
                <td className={styles.td}>{u.name}</td>
                <td className={styles.td}>{u.age}</td>
                <td className={styles.td}>{u.city}</td>
                <td className={styles.td}>${u.income.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

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

export default CampaignDetailPage;
