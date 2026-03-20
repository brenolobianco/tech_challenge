import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import UploadPage from "./components/UploadPage";
import CampaignsPage from "./components/CampaignsPage";
import CampaignDetailPage from "./components/CampaignDetailPage";
import UsersPage from "./components/UsersPage";
import styles from "./App.module.css";

function App() {
  return (
    <BrowserRouter>
      <nav className={styles.nav}>
        <span className={styles.logo}>
          Revfy<span className={styles.logoAccent}>Segment</span>
        </span>
        <NavLink
          to="/"
          className={({ isActive }) => (isActive ? styles.activeLink : styles.link)}
          end
        >
          Upload
        </NavLink>
        <NavLink
          to="/campaigns"
          className={({ isActive }) => (isActive ? styles.activeLink : styles.link)}
        >
          Campaigns
        </NavLink>
        <NavLink
          to="/users"
          className={({ isActive }) => (isActive ? styles.activeLink : styles.link)}
        >
          Users
        </NavLink>
      </nav>
      <div className={styles.container}>
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/campaigns" element={<CampaignsPage />} />
          <Route path="/campaigns/:id" element={<CampaignDetailPage />} />
          <Route path="/users" element={<UsersPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
