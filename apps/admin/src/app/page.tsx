import Link from "next/link";

const stats = [
  { label: "Organisations", value: "184" },
  { label: "Active tenants", value: "94%" },
  { label: "Avg. uptime", value: "99.96%" },
  { label: "Support inbox", value: "12" },
];

const cards = [
  "Platform health",
  "Subscriptions",
  "Feature flags",
  "Integrations",
  "Audit log",
  "Security",
];

export default function AdminHome() {
  return (
    <main className="admin-shell">
      <aside className="admin-sidebar">
        <div className="admin-brand">
          <span className="brand-mark">Z</span>
          <div>
            <strong>Zolexora</strong>
            <small>Platform Admin</small>
          </div>
        </div>
        <nav className="admin-nav">
          <Link href="/" className="active">Dashboard</Link>
          <Link href="/organisations">Organisations</Link>
          <Link href="/users">Users</Link>
          <Link href="/subscriptions">Subscriptions</Link>
          <Link href="/features">Feature Flags</Link>
          <Link href="/integrations">Integrations</Link>
          <Link href="/audit">Audit Logs</Link>
          <Link href="/security">Security</Link>
        </nav>
      </aside>

      <section className="admin-content">
        <header className="admin-topbar">
          <div>
            <p className="eyebrow neutral">Platform control centre</p>
            <h1>System overview</h1>
          </div>
          <button type="button" className="primary-button">Deploy config</button>
        </header>

        <div className="stats-grid">
          {stats.map((stat) => (
            <article key={stat.label} className="stat-card">
              <small>{stat.label}</small>
              <strong>{stat.value}</strong>
            </article>
          ))}
        </div>

        <div className="admin-grid">
          {cards.map((card) => (
            <article key={card} className="admin-panel">
              <h2>{card}</h2>
              <p>Healthy configuration and operational oversight for this platform boundary.</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
