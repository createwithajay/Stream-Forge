function MetricCard({ title, value, description }) {
  return (
    <div className="metric-card">
      <h3>{title}</h3>

      <p className="metric-value">
        {value}
      </p>

      <span>{description}</span>
    </div>
  );
}

export default MetricCard;