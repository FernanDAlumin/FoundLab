import { Activity, BarChart3, Database, FileText } from "lucide-react";

const sections = [
  {
    title: "Assets",
    description: "ETF, A-share stock, and public fund universe.",
    icon: Database
  },
  {
    title: "Backtest Runs",
    description: "Create runs and track execution status.",
    icon: Activity
  },
  {
    title: "Reports",
    description: "Open static HTML, Markdown, chart, and CSV artifacts.",
    icon: FileText
  }
];

export default function App() {
  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>FoundLab</h1>
          <p>Investment decision backtesting dashboard</p>
        </div>
        <span className="icon-button" aria-hidden="true">
          <BarChart3 size={20} />
        </span>
      </header>

      <section className="summary-grid" aria-label="Dashboard sections">
        {sections.map((section) => {
          const Icon = section.icon;
          return (
            <article className="summary-card" key={section.title}>
              <Icon size={22} aria-hidden="true" />
              <h2>{section.title}</h2>
              <p>{section.description}</p>
            </article>
          );
        })}
      </section>
    </main>
  );
}
