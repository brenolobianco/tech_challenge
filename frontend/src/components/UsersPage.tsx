import React, { useState, useEffect, useCallback } from "react";
import { getUsers } from "../api";
import { UserData } from "../types";
import styles from "./UsersPage.module.css";

const UsersPage: React.FC = () => {
  const [users, setUsers] = useState<UserData[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pageSize = 20;

  const [nameFilter, setNameFilter] = useState("");
  const [minAge, setMinAge] = useState("");
  const [maxAge, setMaxAge] = useState("");
  const [minIncome, setMinIncome] = useState("");
  const [maxIncome, setMaxIncome] = useState("");

  const fetchUsers = useCallback(() => {
    const filters: Record<string, string | number> = {};
    if (nameFilter) filters.name = nameFilter;
    if (minAge) filters.min_age = Number(minAge);
    if (maxAge) filters.max_age = Number(maxAge);
    if (minIncome) filters.min_income = Number(minIncome);
    if (maxIncome) filters.max_income = Number(maxIncome);

    setLoading(true);
    setError(null);
    getUsers(page, pageSize, filters)
      .then((resp) => {
        setUsers(resp.data);
        setTotal(resp.total);
      })
      .catch(() => {
        setError("Failed to load users.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [page, nameFilter, minAge, maxAge, minIncome, maxIncome]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleSearch = () => {
    setPage(1);
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      <h2>Users</h2>

      <div className={styles.filtersCard}>
        <span className={styles.filtersLabel}>Filters</span>
        <div className={styles.filtersRow}>
          <input
            placeholder="Name"
            value={nameFilter}
            onChange={(e) => setNameFilter(e.target.value)}
            className={styles.filterInput}
            aria-label="Filter by name"
          />
          <input
            placeholder="Min Age"
            type="number"
            min="0"
            value={minAge}
            onChange={(e) => setMinAge(e.target.value)}
            className={styles.filterInput}
            aria-label="Minimum age"
          />
          <input
            placeholder="Max Age"
            type="number"
            min="0"
            value={maxAge}
            onChange={(e) => setMaxAge(e.target.value)}
            className={styles.filterInput}
            aria-label="Maximum age"
          />
          <input
            placeholder="Min Income"
            type="number"
            min="0"
            value={minIncome}
            onChange={(e) => setMinIncome(e.target.value)}
            className={styles.filterInput}
            aria-label="Minimum income"
          />
          <input
            placeholder="Max Income"
            type="number"
            min="0"
            value={maxIncome}
            onChange={(e) => setMaxIncome(e.target.value)}
            className={styles.filterInput}
            aria-label="Maximum income"
          />
          <button onClick={handleSearch}>Search</button>
        </div>
      </div>

      {error && <div className={styles.errorMessage}>{error}</div>}

      <p className={styles.totalCount}>
        <span className={styles.totalNumber}>{total}</span> users found
      </p>

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
            {loading ? (
              <tr>
                <td colSpan={5} className={styles.emptyCell}>Loading...</td>
              </tr>
            ) : users.length === 0 ? (
              <tr>
                <td colSpan={5} className={styles.emptyCell}>
                  No users found
                </td>
              </tr>
            ) : (
              users.map((u) => (
                <tr key={u.id} className={styles.tr}>
                  <td className={styles.td}>{u.original_id}</td>
                  <td className={styles.td}>{u.name}</td>
                  <td className={styles.td}>{u.age}</td>
                  <td className={styles.td}>{u.city}</td>
                  <td className={styles.td}>${u.income.toFixed(2)}</td>
                </tr>
              ))
            )}
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

export default UsersPage;
