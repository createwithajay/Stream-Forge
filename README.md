# \# Stream-Forge

# 

# \## VisionEdge – Hardware-Accelerated Video Pipeline

# 

# VisionEdge is an Edge AI monitoring system designed to monitor a hardware-accelerated video processing pipeline through a web dashboard.

# 

# The dashboard provides real-time visibility into system metrics, pipeline stages, and camera status.

# 

# \---

# 

# \## Role 5 – Topology \& Dashboard Engineer

# 

# My contribution focused on designing and integrating the monitoring dashboard with the FastAPI backend.

# 

# \### Responsibilities

# 

# \- Built the React monitoring dashboard

# \- Integrated React with FastAPI REST APIs

# \- Added CPU, GPU, memory, and FPS monitoring

# \- Added video pipeline status monitoring

# \- Added camera monitoring for multiple cameras

# \- Implemented LIVE/OFFLINE camera indicators

# \- Added automatic dashboard refresh

# \- Added backend connection/error handling

# \- Tested API endpoints and backend recovery

# \- Improved responsive dashboard layout

# 

# \---

# 

# \## System Architecture

# 

# ```text

# &#x20;                VisionEdge Pipeline

# &#x20;                        |

# &#x20;         +--------------+--------------+

# &#x20;         |              |              |

# &#x20;     Video Input    DeepStream      TensorRT

# &#x20;         |              |              |

# &#x20;         +--------------+--------------+

# &#x20;                        |

# &#x20;                   FastAPI Backend

# &#x20;                        |

# &#x20;             REST API / Monitoring

# &#x20;                        |

# &#x20;                 React Dashboard

# &#x20;                        |

# &#x20;       +----------------+----------------+

# &#x20;       |                |                |

# &#x20;    Metrics          Pipeline          Cameras

# &#x20;    CPU/GPU          Status            Status

# &#x20;    Memory/FPS

