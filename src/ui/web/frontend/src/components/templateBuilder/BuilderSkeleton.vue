<template>
  <div class="builder-skeleton">
    <div class="skeleton-header">
      <div class="skeleton-bar" style="width: 120px; height: 32px;" />
      <div class="skeleton-bar" style="width: 200px; height: 32px; animation-delay: 0.15s;" />
      <div class="skeleton-bar" style="width: 90px; height: 32px; margin-left: auto; animation-delay: 0.3s;" />
    </div>
    <div class="skeleton-tabs">
      <div class="skeleton-bar" style="width: 80px; height: 28px;" />
      <div class="skeleton-bar" style="width: 80px; height: 28px; animation-delay: 0.1s;" />
    </div>
    <div class="skeleton-canvas">
      <!-- Connection lines (drawn after nodes appear) -->
      <svg class="skeleton-connections" viewBox="0 0 900 400" preserveAspectRatio="xMidYMid meet">
        <defs>
          <linearGradient id="eg1" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#6366f1" stop-opacity="0.5" />
            <stop offset="100%" stop-color="#06b6d4" stop-opacity="0.5" />
          </linearGradient>
          <linearGradient id="eg2" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#06b6d4" stop-opacity="0.5" />
            <stop offset="100%" stop-color="#a78bfa" stop-opacity="0.5" />
          </linearGradient>
          <linearGradient id="eg3" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#a78bfa" stop-opacity="0.5" />
            <stop offset="100%" stop-color="#f472b6" stop-opacity="0.5" />
          </linearGradient>
          <linearGradient id="eg4" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#f472b6" stop-opacity="0.5" />
            <stop offset="100%" stop-color="#6366f1" stop-opacity="0.5" />
          </linearGradient>
        </defs>
        <path d="M 255 80 C 310 80, 330 80, 385 80" class="skeleton-edge se-1" stroke="url(#eg1)" />
        <path d="M 490 80 C 540 80, 560 80, 610 80" class="skeleton-edge se-2" stroke="url(#eg2)" />
        <path d="M 490 80 C 520 120, 460 170, 430 200" class="skeleton-edge se-3" stroke="url(#eg3)" />
        <path d="M 715 80 C 740 130, 560 190, 530 200" class="skeleton-edge se-4" stroke="url(#eg4)" />
      </svg>
      <!-- 5 nodes appearing one by one in a loop -->
      <div class="skeleton-node sn-1">
        <div class="skeleton-node-icon sni-indigo" />
        <div class="skeleton-node-lines">
          <div class="skeleton-bar" style="width: 70%; height: 10px;" />
          <div class="skeleton-bar" style="width: 45%; height: 8px; opacity: 0.5;" />
        </div>
      </div>
      <div class="skeleton-node sn-2">
        <div class="skeleton-node-icon sni-cyan" />
        <div class="skeleton-node-lines">
          <div class="skeleton-bar" style="width: 60%; height: 10px;" />
          <div class="skeleton-bar" style="width: 50%; height: 8px; opacity: 0.5;" />
        </div>
      </div>
      <div class="skeleton-node sn-3">
        <div class="skeleton-node-icon sni-violet" />
        <div class="skeleton-node-lines">
          <div class="skeleton-bar" style="width: 55%; height: 10px;" />
          <div class="skeleton-bar" style="width: 40%; height: 8px; opacity: 0.5;" />
        </div>
      </div>
      <div class="skeleton-node sn-4">
        <div class="skeleton-node-icon sni-pink" />
        <div class="skeleton-node-lines">
          <div class="skeleton-bar" style="width: 65%; height: 10px;" />
          <div class="skeleton-bar" style="width: 48%; height: 8px; opacity: 0.5;" />
        </div>
      </div>
      <div class="skeleton-node sn-5">
        <div class="skeleton-node-icon sni-indigo" />
        <div class="skeleton-node-lines">
          <div class="skeleton-bar" style="width: 75%; height: 10px;" />
          <div class="skeleton-bar" style="width: 42%; height: 8px; opacity: 0.5;" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.builder-skeleton {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 0;
  background: #0f172a;
}

.skeleton-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid #1e293b;
}

.skeleton-tabs {
  display: flex;
  gap: 8px;
  padding: 8px 16px;
  border-bottom: 1px solid #1e293b;
}

.skeleton-bar {
  background: linear-gradient(90deg, #1e293b 0%, #334155 50%, #1e293b 100%);
  background-size: 200% 100%;
  border-radius: 6px;
  animation: skeleton-shimmer 1.8s ease-in-out infinite;
}

.skeleton-canvas {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: radial-gradient(circle at 1px 1px, rgba(30, 41, 59, 0.5) 1px, transparent 0);
  background-size: 24px 24px;
}

.skeleton-connections {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.skeleton-edge {
  fill: none;
  stroke-width: 2;
  stroke-dasharray: 200;
  stroke-dashoffset: 200;
  opacity: 0;
  animation: skeleton-edge-cycle 5s ease infinite;
}
.se-1 { animation-delay: 0.5s; }
.se-2 { animation-delay: 1.0s; }
.se-3 { animation-delay: 1.0s; }
.se-4 { animation-delay: 1.5s; }

.skeleton-node {
  position: absolute;
  width: 170px;
  height: 64px;
  background: rgba(15, 23, 42, 0.95);
  border-radius: 10px;
  border: 1px solid #334155;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px;
  opacity: 0;
  transform: translateY(12px) scale(0.92);
  animation: skeleton-node-cycle 5s ease infinite;
}

.sn-1 { top: 16%; left: 14%; animation-delay: 0s; }
.sn-2 { top: 16%; left: 40%; animation-delay: 0.5s; }
.sn-3 { top: 16%; left: 66%; animation-delay: 1.0s; }
.sn-4 { top: 48%; left: 27%; animation-delay: 1.5s; }
.sn-5 { top: 48%; left: 53%; animation-delay: 2.0s; }

.skeleton-node-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  flex-shrink: 0;
}

.sni-indigo { background: linear-gradient(135deg, #4f46e5, #818cf8); }
.sni-cyan   { background: linear-gradient(135deg, #0891b2, #22d3ee); }
.sni-violet { background: linear-gradient(135deg, #7c3aed, #c4b5fd); }
.sni-pink   { background: linear-gradient(135deg, #db2777, #f9a8d4); }

.skeleton-node-lines {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@keyframes skeleton-node-cycle {
  0%   { opacity: 0; transform: translateY(12px) scale(0.92); }
  8%   { opacity: 1; transform: translateY(0) scale(1); }
  70%  { opacity: 1; transform: translateY(0) scale(1); }
  85%  { opacity: 0; transform: translateY(-6px) scale(0.96); }
  100% { opacity: 0; transform: translateY(12px) scale(0.92); }
}

@keyframes skeleton-edge-cycle {
  0%   { opacity: 0; stroke-dashoffset: 200; }
  10%  { opacity: 0.8; stroke-dashoffset: 200; }
  40%  { opacity: 0.8; stroke-dashoffset: 0; }
  70%  { opacity: 0.8; stroke-dashoffset: 0; }
  85%  { opacity: 0; stroke-dashoffset: 0; }
  100% { opacity: 0; stroke-dashoffset: 200; }
}
</style>
