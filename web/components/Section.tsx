import { CATEGORIES, type EpistemicCategory } from "@/lib/categories";

export function Legend() {
  return (
    <div className="legend">
      {Object.values(CATEGORIES).map((category) => (
        <div className={`item cat-${category.id}`} key={category.id}>
          <span className={`badge badge-${category.id}`}>{category.label}</span>
          <p>{category.description}</p>
        </div>
      ))}
    </div>
  );
}

export function Section({
  category,
  title,
  hint,
  count,
  children,
}: {
  category: EpistemicCategory;
  title: string;
  hint?: string;
  count?: number;
  children: React.ReactNode;
}) {
  return (
    <section className={`section cat-${category}`}>
      <div className="section-head">
        <h2>{title}</h2>
        {typeof count === "number" ? <span className="badge">{count}</span> : null}
        {hint ? <span className="hint">{hint}</span> : null}
      </div>
      <div className="section-body">{children}</div>
    </section>
  );
}

export function Row({ name, meta, detail }: { name: string; meta?: string; detail?: unknown }) {
  return (
    <div className="row">
      <div className="name">{name}</div>
      {meta ? <div className="meta">{meta}</div> : null}
      {detail !== undefined ? <pre>{JSON.stringify(detail, null, 2)}</pre> : null}
    </div>
  );
}
