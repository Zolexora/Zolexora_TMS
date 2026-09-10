import Link from "next/link";

const solutions = ["Employee transport", "Spot & fixed booking", "Rental operations", "Corporate travel", "Airport transfer", "Outstation trips"];
const features = [
  ["01", "Operations control", "Move from request to duty, dispatch, trip and completion without losing the thread."],
  ["02", "Financial clarity", "Turn completed work into accurate bills, invoices, collections and profit visibility."],
  ["03", "Built for teams", "Keep commanders, dispatchers, drivers and finance working from one secure source of truth."],
];

export default function Home() {
  return (
    <main className="site-shell">
      <nav className="nav wrap">
        <Link className="brand" href="/" aria-label="Zolexora TMS home"><span className="brand-mark">Z</span><span>Zolexora <em>TMS</em></span></Link>
        <div className="nav-links"><a href="#solutions">Solutions</a><a href="#platform">Platform</a><a href="#roadmap">Roadmap</a></div>
        <div className="nav-actions"><Link className="text-link" href="/login">Sign in</Link><Link className="button button-small" href="/onboarding">Get started <span>↗</span></Link></div>
      </nav>

      <section className="hero wrap">
        <div className="hero-copy"><p className="eyebrow"><span className="pulse-dot" /> The operating system for transport teams</p><h1>Complete transport management. <span>One powerful platform.</span></h1><p className="hero-text">Zolexora brings bookings, employee transport, fleet, drivers, operations, billing, payments and reporting into one unified system.</p><div className="hero-actions"><Link className="button" href="/onboarding">Build your workspace <span>↗</span></Link><Link className="button button-quiet" href="/login">Explore the platform <span>→</span></Link></div><div className="hero-meta"><span>Built for every trip</span><i /> <span>Secure by design</span><i /> <span>Ready to scale</span></div></div>
        <div className="hero-visual" aria-label="A preview of the Zolexora operations dashboard"><div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="preview-card"><div className="preview-top"><span className="mini-brand">Z</span><span>Tuesday, 14 October</span><b>•••</b></div><div className="preview-heading"><div><small>OPERATIONS OVERVIEW</small><h2>Good morning, Aisha.</h2></div><span className="avatar">AS</span></div><div className="metric-grid"><div><small>ACTIVE DUTIES</small><strong>24</strong><span className="up">+12.5%</span></div><div><small>ON THE ROAD</small><strong>18</strong><span className="neutral">75% of fleet</span></div><div><small>THIS MONTH</small><strong>₹8.4L</strong><span className="up">+8.2%</span></div></div><div className="chart-panel"><div className="chart-label"><span>Trip volume</span><span>Last 7 days <b>⌄</b></span></div><div className="bars">{[42, 60, 48, 78, 55, 88, 70].map((height, index) => <i key={index} style={{ height: `${height}%` }} />)}</div><div className="chart-days"><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span><span>Mon</span><span>Tue</span></div></div><div className="activity"><span className="activity-icon green">✓</span><div><b>Duty #D-1048 completed</b><small>Airport transfer · 2 min ago</small></div><span className="activity-amount">₹3,240</span></div></div></div>
      </section>

      <section className="solution-band" id="solutions"><div className="wrap"><div className="section-intro"><p className="eyebrow">One system, every journey</p><h2>Designed around how transport businesses actually run.</h2><p>From the first customer request to the final payment reconciliation, every moving part stays connected.</p></div><div className="solution-list">{solutions.map((solution, index) => <div className="solution-item" key={solution}><span>0{index + 1}</span><b>{solution}</b><i>↗</i></div>)}</div></div></section>
      <section className="feature-section wrap" id="platform"><div className="feature-header"><p className="eyebrow">The Zolexora difference</p><h2>Less chasing. More moving.</h2></div><div className="feature-grid">{features.map(([number, title, copy]) => <article key={number}><span className="feature-number">{number}</span><h3>{title}</h3><p>{copy}</p><span className="feature-arrow">↗</span></article>)}</div></section>
      <section className="cta-section wrap" id="roadmap"><div><p className="eyebrow">Your next trip starts here</p><h2>Ready to run transport<br /><span>with clarity?</span></h2></div><Link className="button button-light" href="/onboarding">Create your organisation <span>↗</span></Link></section>
      <footer className="footer wrap"><span>© 2026 Zolexora TMS</span><span>Transport, connected.</span><span>Built for the road ahead.</span></footer>
    </main>
  );
}
