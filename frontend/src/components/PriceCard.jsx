export default function PriceCard({ item, onClick }) {
  const up = item.change > 0;
  const down = item.change < 0;
  const badgeClass = up ? "badge up" : down ? "badge down" : "badge same";
  const arrow = up ? "\u25B2" : down ? "\u25BC" : "\u2013";

  return (
    <div className="card" onClick={onClick}>
      <div className="card-top">
        <h3>{item.name}</h3>
        <span className={"tag " + item.category}>{item.category}</span>
      </div>

      <div className="price">
        {"\u20B9"} {item.price.toFixed(2)} <small>/ {item.unit}</small>
      </div>

      <div className="range">
        Range: {"\u20B9"}{item.min_price?.toFixed(2)} - {"\u20B9"}{item.max_price?.toFixed(2)}
      </div>

      <div className="card-bottom">
        <span className={badgeClass}>
          {arrow} {item.change_pct === null ? "no change data" : Math.abs(item.change_pct) + "%"}
        </span>
        <span className="date">{item.date}</span>
      </div>
    </div>
  );
}