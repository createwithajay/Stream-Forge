function Header() {
  return (
    <header className="header">
      <div>
        <h1>VisionEdge</h1>
        <p>Real-Time Edge AI Monitoring</p>
      </div>

      <div className="system-status">
        <span className="status-dot"></span>
        System Online
      </div>
    </header>
  );
}

export default Header;