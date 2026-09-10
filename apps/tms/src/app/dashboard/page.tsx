import Link from "next/link";

const metrics = [
  { label: "Active duties", value: "24", change: "+12.5%" },
  { label: "Vehicles on road", value: "18", change: "75% fleet" },
  { label: "Outstanding invoices", value: "₹8.4L", change: "+8.2%" },
];

const jobs = [
  { status: "Accepted", title: "Airport transfer · Duty #D-1048", owner: "A. Khan", time: "2 min ago" },
  { status: "Assigned", title: "Corporate route · Duty #D-1051", owner: "Dispatch", time: "12 min ago" },
  { status: "Pending", title: "Outstation return · Duty #D-1058", owner: "Ops team", time: "Awaiting acceptance" },
];

export default function DashboardPage() {
  return (
    <main className="dashboard-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-mark">Z</span>
          <div>
            <strong>Zolexora</strong>
            <small>TMS</small>
          </div>
        </div>

        <nav className="sidebar-nav">
          <Link href="/dashboard" className="active">Dashboard</Link>
          <Link href="/dashboard/operations">Operations</Link>
          <Link href="/dashboard/fleet">Fleet</Link>
          <Link href="/dashboard/drivers">Drivers</Link>
          <Link href="/dashboard/finance">Finance</Link>
          <Link href="/dashboard/reports">Reports</Link>
          <Link href="/dashboard/organisation">Organisation</Link>
        </nav>
      </aside>

      <section className="dashboard-content">
        <header className="topbar">
          <div>
            <p className="eyebrow neutral">Operations overview</p>
            <h1>Good morning, Aisha.</h1>
          </div>
          <div className="topbar-actions">
            <button type="button" className="secondary-button">Export report</button>
            <button type="button" className="primary-button">Create booking</button>
          </div>
        </header>

        <div className="metric-grid dashboard-metrics">
          {metrics.map((metric) => (
            <article key={metric.label} className="metric-card">
              <small>{metric.label}</small>
              <strong>{metric.value}</strong>
              <span>{metric.change}</span>
            </article>
          ))}
        </div>

        <div className="panel-grid">
          <section className="panel panel-large">
            <div className="panel-header">
              <h2>Trip volume</h2>
              <span>Last 7 days</span>
            </div>
            <div className="mini-bars">
              {[42, 60, 48, 78, 55, 88, 70].map((height, index) => (
                <span key={index} style={{ height: `${height}%` }} />
              ))}
            </div>
          </section>

          <section className="panel">
            <div className="panel-header">
              <h2>Priority actions</h2>
              <span>Today</span>
            </div>
            <ul className="action-list">
              <li>Verify 4 pending driver acceptances</li>
              <li>Review 2 invoice approvals</li>
              <li>Check vehicle maintenance list</li>
            </ul>
          </section>
        </div>

        <section className="panel">
          <div className="panel-header">
            <h2>Latest operational activity</h2>
            <span>Updated now</span>
          </div>
          <div className="job-list">
            {jobs.map((job) => (
              <div className="job-row" key={job.title}>
                <span className={`status-badge ${job.status.toLowerCase()}`}>{job.status}</span>
                <div>
                  <strong>{job.title}</strong>
                  <small>{job.owner}</small>
                </div>
                <time>{job.time}</time>
              </div>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}
